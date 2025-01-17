from __future__ import annotations

from json import dumps
from json import loads
from onegov.websockets import log


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from websockets.legacy.client import WebSocketClientProtocol


async def acknowledged(websocket: WebSocketClientProtocol) -> None:
    """ Wait for an OK from the server. """

    message = await websocket.recv()
    try:
        assert loads(message)['type'] == 'acknowledged'
    except Exception as exception:
        # FIXME: technically message can be bytes
        log.error(f'Unexpected response: {message}')  # type:ignore
        await websocket.close()
        raise OSError(message) from exception


async def register(
    websocket: WebSocketClientProtocol,
    schema: str,
    channel: str | None
) -> None:
    """ Registers for broadcast messages. """

    await websocket.send(
        dumps({
            'type': 'register',
            'schema': schema,
            'channel': channel
        })
    )
    await acknowledged(websocket)


async def authenticate(
    websocket: WebSocketClientProtocol,
    token: str
) -> None:
    """ Authenticates with the given token. """

    await websocket.send(
        dumps({
            'type': 'authenticate',
            'token': token
        })
    )
    await acknowledged(websocket)


async def broadcast(
    websocket: WebSocketClientProtocol,
    schema: str,
    channel: str | None,
    message: JSON_ro
) -> None:
    """ Broadcasts the given message to all connected clients.

    Assumes prior authentication.

    """

    await websocket.send(
        dumps({
            'type': 'broadcast',
            'schema': schema,
            'channel': channel,
            'message': message
        })
    )
    await acknowledged(websocket)


async def status(websocket: WebSocketClientProtocol) -> str | None:
    """ Receives the status of the server.

    Assumes prior authentication.

    """

    await websocket.send(
        dumps({
            'type': 'status',
        })
    )
    await acknowledged(websocket)
    message = await websocket.recv()
    try:
        payload = loads(message)
        assert payload['type'] == 'status'
        assert payload['message']
    except Exception:
        # FIXME: technically message can be bytes
        log.error(f'Unexpected response: {message}')  # type:ignore
        await websocket.close()
        return None
    else:
        return payload['message']
