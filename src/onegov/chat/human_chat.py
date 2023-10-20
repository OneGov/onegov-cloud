import asyncio
import websockets


connected_clients = []


async def handle_connection(websocket, path):
    # Add the websocket to a list of connected clients
    connected_clients.append(websocket)
    try:
        while True:
            # Receive a message from the client
            message = await websocket.recv()

            # Broadcast the message to all connected clients
            for client in connected_clients:
                await client.send(message)
    finally:
        # Remove the websocket from the list of connected clients
        connected_clients.remove(websocket)
