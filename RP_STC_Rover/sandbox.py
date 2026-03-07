# TODO:
# GPIO outputs to motor driver based off of inputs
# USB Camera/Microphone
# USB Speaker

import asyncio
import websockets

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            # Ensure we have a binary message of length 5
            if isinstance(message, bytes) and len(message) == 5:
                opcode, motor_number, power, pwm, direction = message
                print(f"Opcode: {opcode}, Motor: {motor_number}, "
                      f"Power: {power}, PWM: {pwm}, Direction: {direction}")
            else:
                print(f"Received raw message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8081):
        print("WebSocket server running on ws://0.0.0.0:8081")
        await asyncio.Future()  # run forever

asyncio.run(main())