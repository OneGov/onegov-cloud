from __future__ import annotations

from json import dumps
from json import loads
from onegov.websockets import log


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from websockets.asyncio.client import ClientConnection


async def acknowledged(websocket: ClientConnection) -> None:
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
    websocket: ClientConnection,
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
    websocket: ClientConnection,
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
    websocket: ClientConnection,
    schema: str,
    channel: str | None,
    message: JSON_ro,
    groupids: list[str] | None = None
) -> None:
    """ Broadcasts the given message to all connected clients.

    Optionally can be filtered to a list of groupids, for users with
    a lower privilege level like editors or members. admins will always
    receive all broadcasts in channels they've subscribed to.

    Assumes prior authentication.

    """

    await websocket.send(
        dumps({
            'type': 'broadcast',
            'schema': schema,
            'channel': channel,
            'message': message,
            'groupids': groupids,
        })
    )
    await acknowledged(websocket)


async def status(websocket: ClientConnection) -> str | None:
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
