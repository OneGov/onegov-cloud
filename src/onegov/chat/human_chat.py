from onegov.websockets import log
import json
# from onegov.org import OrgApp

connected_clients = []


async def handle_chat(websocket, payload):
    """
    Handle chat server handler.
    """
    log.debug(f"Listening for chat messages for user: {websocket.id}")
    log.debug(payload)

    while True:
        message = await websocket.recv()
        print(f'I got the message {message}')
        await websocket.send(json.dumps({
            'type': "message",
            'message': message,
            'user': "Haku",
            'time': 'now',
        }))
