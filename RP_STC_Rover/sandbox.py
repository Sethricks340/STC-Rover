import asyncio
import websockets

# Motor commands
async def motor_handler(websocket, path):
    if path != "/motors":  # Only handle motor endpoint
        return
    print(f"Motor client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            if isinstance(message, bytes) and len(message) == 5:
                opcode, motor_number, power, pwm, direction = message
                print(f"Opcode: {opcode}, Motor: {motor_number}, "
                      f"Power: {power}, PWM: {pwm}, Direction: {direction}")
            else:
                print(f"Received raw motor message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Motor client disconnected: {websocket.remote_address}")

# Audio data
async def audio_handler(websocket, path):
    if path != "/audio":  # Only handle audio endpoint
        return
    print(f"Audio client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received audio chunk of length {len(message)}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Audio client disconnected: {websocket.remote_address}")

async def main():
    # Single server handling multiple paths
    async with websockets.serve(motor_handler, "0.0.0.0", 8081):
        async with websockets.serve(audio_handler, "0.0.0.0", 8082):
            print("Motor WS: ws://0.0.0.0:8081/motors")
            print("Audio WS: ws://0.0.0.0:8082/audio")
            await asyncio.Future()  # run forever

asyncio.run(main())