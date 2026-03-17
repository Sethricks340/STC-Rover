import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd
import signal
import sys

TAILSCALE_IP = "0.0.0.0"  # bind to all interfaces
MIC_PORT = 8766

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_BLOCKSIZE = 1024

# Choose output device (USB speaker or default)
speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:  # replace with your speaker name
        speaker_index = i
        print("Using speaker device:", speaker_index, sd.query_devices()[speaker_index])
        break
if speaker_index is None:
    speaker_index = sd.default.device[1]  # fallback default output

# global audio stream
audio_stream = sd.OutputStream(device=speaker_index,
                               samplerate=AUDIO_RATE,
                               channels=AUDIO_CHANNELS,
                               blocksize=AUDIO_BLOCKSIZE)
audio_stream.start()


async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                audio_bytes = base64.b64decode(message[4:])
                audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                print("Received chunk:", len(audio_array))
                audio_array = np.clip(audio_array * 3.0, -1.0, 1.0)  # optional gain
                audio_stream.write(audio_array)
            else:
                print(f"Received raw message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")


async def main():
    async with websockets.serve(handler, TAILSCALE_IP, MIC_PORT, ping_interval=None):
        print(f"Microphone WebSocket server running on ws://{TAILSCALE_IP}:{MIC_PORT}")
        await asyncio.Future()  # run forever


def cleanup():
    print("Stopping audio stream...")
    audio_stream.stop()
    audio_stream.close()


def handle_exit(signum, frame):
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except asyncio.CancelledError:
    pass
finally:
    cleanup()