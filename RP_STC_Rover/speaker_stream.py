import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd
import signal
import sys

TAILSCALE_IP = "0.0.0.0"
MIC_PORT = 8766

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_BLOCKSIZE = 1024

# --- Choose output device ---
speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:
        speaker_index = i
        print("Using speaker device:", speaker_index, dev)
        break
if speaker_index is None:
    speaker_index = sd.default.device[1]

# --- Async queue for audio chunks ---
audio_queue = asyncio.Queue()

# --- Non-blocking OutputStream ---
def output_callback(outdata, frames, time, status):
    try:
        chunk = audio_queue.get_nowait()
        if len(chunk) < len(outdata):
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):].fill(0)
        else:
            outdata[:] = chunk
    except asyncio.QueueEmpty:
        outdata.fill(0)  # silence if no data

audio_stream = sd.OutputStream(
    device=speaker_index,
    samplerate=AUDIO_RATE,
    channels=AUDIO_CHANNELS,
    blocksize=AUDIO_BLOCKSIZE,
    callback=output_callback
)
audio_stream.start()

# --- WebSocket handler ---
async def handler(websocket):
    addr = websocket.remote_address
    print(f"Client connected: {addr}")
    try:
        async for message in websocket:
            if isinstance(message, str):
                message = message.encode('ascii')
            audio_bytes = base64.b64decode(message)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            # optional gain
            audio_array = np.clip(audio_array * 1.0, -1.0, 1.0)
            audio_array = audio_array.reshape(-1, AUDIO_CHANNELS)
            audio_queue.put_nowait(audio_array)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {addr}")

# --- Async server ---
async def main():
    async with websockets.serve(handler, TAILSCALE_IP, MIC_PORT, ping_interval=None):
        print(f"Microphone WebSocket server running on ws://{TAILSCALE_IP}:{MIC_PORT}")
        await asyncio.Future()  # run forever

# --- Cleanup ---
def cleanup():
    print("Stopping audio stream...")
    audio_stream.stop()
    audio_stream.close()

def handle_exit(signum, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# --- Run event loop ---
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except asyncio.CancelledError:
    pass
finally:
    cleanup()