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
<<<<<<< Updated upstream
=======


# # Start the WebSocket server
# start_server = websockets.serve(handle_connection, 'localhost', 8000)
# # Run the server indefinitely
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()


# async def connect_to_server():
#     async with websockets.connect('ws://localhost:8000') as websocket:
#         while True:
#             # Get user input
#             message = input("Enter message: ")

#             # Send the message to the server
#             await websocket.send(message)

#             # Receive a message from the server
#             response = await websocket.recv()

#             # Print the received message
#             print("Received:", response)


# # Connect the WebSocket client
# asyncio.get_event_loop().run_until_complete(connect_to_server())
>>>>>>> Stashed changes
