from asyncio import Future
from asyncio import run
from json import dumps
from json import loads
from logging import basicConfig
from logging import DEBUG
from onegov.websockets import log
from websockets import broadcast
from websockets import serve


CONNECTIONS = {}
TOKEN = ''


def get_payload(message, expected):
    """ Deserialize JSON payload and check type. """

    try:
        payload = loads(message)
        assert payload['type'] in expected
        return payload
    except Exception:
        pass


async def error(websocket, message, close=True):
    """ Sends an error. """

    await websocket.send(
        dumps({
            'type': 'error',
            'message': message
        })
    )
    if close:
        await websocket.close()


async def acknowledge(websocket):
    """ Sends an acknowledge. """

    await websocket.send(
        dumps({
            'type': 'acknowledged'
        })
    )


async def handle_listen(websocket, payload):
    """ Handles listening clients. """

    assert payload.get('type') == 'register'

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    await acknowledge(websocket)

    log.debug(f'{websocket.id} listens @ {schema}')
    connections = CONNECTIONS.setdefault(schema, set())
    connections.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connections = CONNECTIONS.setdefault(schema, set())
        if websocket in connections:
            connections.remove(websocket)


async def handle_authentication(websocket, payload):
    """ Handles authentication. """

    assert payload.get('type') == 'authenticate'

    token = payload.get('token')
    if not token or not token == TOKEN:
        await error(websocket, 'authentication failed')
        return

    await acknowledge(websocket)

    log.debug(f'{websocket.id} authenticated')


async def handle_status(websocket, payload):
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


async def handle_broadcast(websocket, payload):
    """ Handles broadcasts. """

    assert payload.get('type') == 'broadcast'

    message = payload.get('message')
    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, 'invalid schema')
        return

    await acknowledge(websocket)

    connections = CONNECTIONS.get(schema, set())
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
        f' to {len(connections)} receiver(s) @ {schema}'
    )


async def handle_manage(websocket, payload):
    """ Handles managing clients. """

    await handle_authentication(websocket, payload)

    async for message in websocket:
        payload = get_payload(message, ('broadcast', 'status'))
        if payload and payload['type'] == 'broadcast':
            await handle_broadcast(websocket, payload)
        elif payload and payload['type'] == 'status':
            await handle_status(websocket, payload)
        else:
            await error(websocket, f'invalid command: {message}')


async def handle_start(websocket):
    log.debug(f'{websocket.id} connected')
    message = await websocket.recv()
    payload = get_payload(message, ('authenticate', 'register'))
    if payload and payload['type'] == 'authenticate':
        await handle_manage(websocket, payload)
    elif payload and payload['type'] == 'register':
        await handle_listen(websocket, payload)
    else:
        await error(websocket, f'invalid command: {message}')
    log.debug(f'{websocket.id} disconnected')


async def main(host='localhost', port=8765, token=None):
    assert token, "Please provide a token!"
    global TOKEN
    TOKEN = token
    log.debug(f'Serving on ws://{host}:{port}')
    async with serve(handle_start, host, port):
        await Future()


# todo: remove me?
if __name__ == "__main__":
    basicConfig()
    log.setLevel(DEBUG)
    run(main(token='token'))
