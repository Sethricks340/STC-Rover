import asyncio
import websockets

async def handler(websocket):
    path = websocket.path  # get the path the client connected to
    print(f"Client connected: {websocket.remote_address} on {path}")

    try:
        async for message in websocket:
            if path == "/motors":
                if isinstance(message, bytes) and len(message) == 5:
                    opcode, motor_number, power, pwm, direction = message
                    print(f"Opcode: {opcode}, Motor: {motor_number}, Power: {power}, PWM: {pwm}, Direction: {direction}")
                else:
                    print(f"Motor raw: {message}")
            elif path == "/audio":
                print(f"Audio chunk length: {len(message)}")
            else:
                print(f"Unknown path {path}, message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8081):
        print("WebSocket server running on ws://0.0.0.0:8081 with /motors and /audio paths")
        await asyncio.Future()  # run forever

asyncio.run(main())