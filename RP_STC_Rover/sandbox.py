import asyncio
import websockets

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8081):
        print("WebSocket server running on ws://0.0.0.0:8081")
        await asyncio.Future()  # run forever

asyncio.run(main())