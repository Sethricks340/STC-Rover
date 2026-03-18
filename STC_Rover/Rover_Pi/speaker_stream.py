# TODO:
#   Run on reboot 

# ---- To be run on car (Pi) ---- 


import asyncio
import websockets
import signal
import sys
import time
import base64
import numpy as np
import sounddevice as sd

PORT = 8766 

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1

speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:
        speaker_index = i
        print("Connected to UACDemoV1 speaker")
        break

if speaker_index is None:
    print("USB speaker not found, using default output")
    speaker_index = sd.default.device[1]  # output device

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")

    audio_stream = sd.OutputStream(
        device=speaker_index,
        samplerate=AUDIO_RATE,
        channels=AUDIO_CHANNELS
    )
    audio_stream.start()

    try:
        async for data in websocket:
            if isinstance(data, str) and data.startswith("MIC:"):
                audio_bytes = base64.b64decode(data[4:])
                audio_array = np.frombuffer(audio_bytes, dtype=np.float32).reshape(-1, AUDIO_CHANNELS)
                
                # Apply gain first
                gain = 1.0
                audio_array = np.clip(audio_array * gain, -1.0, 1.0)
                
                # Write only once
                audio_stream.write(audio_array)
            else:
                print(f"Received raw message: {data}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        audio_stream.stop()
        audio_stream.close()

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None):
        print(f"WebSocket server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # run forever

def cleanup():
    print("Cleaning up GPIO and cancelling tasks...")
    # TODO: update cancelling tasks
    # pwmA.stop()
    # pwmB.stop()
    # GPIO.cleanup()

def handle_exit(signum, frame):
    for task in asyncio.all_tasks():
        task.cancel()
    cleanup()
    sys.exit(0)

# Signal handling
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cleanup()