from json import dumps
from json import loads
from onegov.websockets import log


async def acknowledged(websocket, fail=False):
    """ Wait for an OK from the server. """

    message = await websocket.recv()
    try:
        assert loads(message)['type'] == 'acknowledged'
    except Exception:
        log.error(f'Unexpected response: {message}')
        await websocket.close()
        if fail:
            raise IOError(message)


async def register(websocket, schema):
    """ Registers for broadcast messages. """

    await websocket.send(
        dumps({
            'type': 'register',
            'schema': schema
        })
    )
    await acknowledged(websocket)


async def authenticate(websocket, token):
    """ Authenticates with the given token. """

    await websocket.send(
        dumps({
            'type': 'authenticate',
            'token': token
        })
    )
    await acknowledged(websocket, fail=True)


async def broadcast(websocket, schema, message):
    """ Broadcasts the given message to all connected clients.

    Assumes prior authentication.

    """

    await websocket.send(
        dumps({
            'type': 'broadcast',
            'schema': schema,
            'message': message
        })
    )
    await acknowledged(websocket)


async def status(websocket):
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
        log.error(f'Unexpected response: {message}')
        await websocket.close()
    else:
        return payload['message']
