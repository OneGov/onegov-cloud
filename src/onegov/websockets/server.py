from asyncio import Future
from json import dumps
from json import loads
from onegov.websockets import log
from websockets.legacy.protocol import broadcast
from websockets.legacy.server import serve
from onegov.chat.human_chat import handle_chat


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.types import JSONObject
    from onegov.core.types import JSONObject_ro
    from websockets.legacy.server import WebSocketServerProtocol


CONNECTIONS: dict[str, set['WebSocketServerProtocol']] = {}
TOKEN = ''  # nosec: B105


def get_payload(
    message: str | bytes,
    expected: 'Collection[str]'
) -> 'JSONObject | None':
    """ Deserialize JSON payload and check type. """

    try:
        payload = loads(message)
        assert payload['type'] in expected
        return payload
    except Exception:
        log.warning('Invalid payload received')
        return None


async def error(
    websocket: 'WebSocketServerProtocol',
    message: str,
    close: bool = True
) -> None:
    """ Sends an error. """

    await websocket.send(
        dumps({
            'type': 'error',
            'message': message
        })
    )
    if close:
        await websocket.close()


async def acknowledge(websocket: 'WebSocketServerProtocol') -> None:
    """ Sends an acknowledge. """

    await websocket.send(
        dumps({
            'type': 'acknowledged'
        })
    )


async def handle_listen(
    websocket: 'WebSocketServerProtocol',
    payload: 'JSONObject_ro'
) -> None:
    """ Handles listening clients. """

    assert payload.get('type') == 'register'

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    channel = payload.get('channel')
    if channel is not None and not isinstance(channel, str):
        await error(websocket, f'invalid channel: {channel}')
        return

    await acknowledge(websocket)

    schema_channel = f'{schema}-{channel}' if channel else schema
    log.debug(f'{websocket.id} listens @ {schema_channel}')
    log.debug(payload)
    connections = CONNECTIONS.setdefault(schema_channel, set())
    connections.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connections = CONNECTIONS.setdefault(schema_channel, set())
        if websocket in connections:
            connections.remove(websocket)


async def handle_authentication(
    websocket: 'WebSocketServerProtocol',
    payload: 'JSONObject_ro'
) -> None:
    """ Handles authentication. """

    assert payload.get('type') == 'authenticate'

    token = payload.get('token')
    if not token or not isinstance(token, str):
        await error(websocket, 'invalid token')
        return
    if token != TOKEN:
        await error(websocket, 'authentication failed')
        return

    await acknowledge(websocket)

    log.debug(f'{websocket.id} authenticated')


async def handle_status(
    websocket: 'WebSocketServerProtocol',
    payload: 'JSONObject_ro'
) -> None:
    """ Handles status requests. """

    assert payload.get('type') == 'status'

    await acknowledge(websocket)

    await websocket.send(
        dumps({
            'type': 'status',
            'message': {
                'connections': {
                    key: len(values)
                    for key, values in CONNECTIONS.items()
                }
            }
        })
    )

    log.debug(f'{websocket.id} status sent')


async def handle_broadcast(
    websocket: 'WebSocketServerProtocol',
    payload: 'JSONObject_ro'
) -> None:
    """ Handles broadcasts. """

    assert payload.get('type') == 'broadcast'

    message = payload.get('message')
    schema = payload.get('schema')
    channel = payload.get('channel')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return
    if channel is not None and not isinstance(channel, str):
        await error(websocket, f'invalid channel: {channel}')
        return
    if not message:
        await error(websocket, 'missing message')
        return

    await acknowledge(websocket)

    schema_channel = f'{schema}-{channel}' if channel else schema
    connections = CONNECTIONS.get(schema_channel, set())
    if connections:
        broadcast(
            connections,
            dumps({
                'type': 'notification',
                'message': message
            })
        )

    log.debug(
        f'{websocket.id} sent {message}'
        f' to {len(connections)} receiver(s) @ {schema_channel}'
    )


async def handle_manage(
    websocket: 'WebSocketServerProtocol',
    authentication_payload: 'JSONObject_ro'
) -> None:
    """ Handles managing clients. """

    await handle_authentication(websocket, authentication_payload)

    async for message in websocket:
        payload = get_payload(message, ('broadcast', 'status'))
        if payload and payload['type'] == 'broadcast':
            await handle_broadcast(websocket, payload)
        elif payload and payload['type'] == 'status':
            await handle_status(websocket, payload)
        else:
            await error(
                websocket,
                # FIXME: technically message can be bytes
                f'invalid command: {message}'  # type:ignore
            )


async def handle_start(websocket: 'WebSocketServerProtocol') -> None:
    log.debug(f'{websocket.id} connected')
    message = await websocket.recv()
    payload = get_payload(message, ('authenticate', 'register', 'chat'))
    if payload and payload['type'] == 'authenticate':
        await handle_manage(websocket, payload)
    elif payload and payload['type'] == 'register':
        await handle_listen(websocket, payload)
    elif payload and payload['type'] == 'chat':
        await handle_chat(websocket, payload)
    else:
        # FIXME: technically message can be bytes
        await error(websocket, f'invalid command: {message}')  # type:ignore
    log.debug(payload)
    log.debug(f'{websocket.id} disconnected')


async def main(host: str, port: int, token: str) -> None:
    global TOKEN
    TOKEN = token
    log.debug(f'Serving on ws://{host}:{port}')
    async with serve(handle_start, host, port):
        await Future()
