import asyncio
import websockets

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received: {message}")
            # Example: echo back to all clients
            await asyncio.wait([client.send(message) for client in connected_clients])
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 81):
        print("WebSocket server running on ws://0.0.0.0:81/ws")
        await asyncio.Future()  # run forever

asyncio.run(main())