import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd

PORT = 8766
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
# BLOCKSIZE = 512
BLOCKSIZE = 1024

# USB speaker
speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:
        speaker_index = i
        print(f"Connected to USB speaker at index {i}")
        break
if speaker_index is None:
    raise RuntimeError("USB speaker not found")

# Audio queue
audio_buffer = asyncio.Queue()

def audio_callback(outdata, frames, time, status):
    try:
        chunk = audio_buffer.get_nowait()
        if len(chunk) < frames:
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):] = 0
        else:
            outdata[:] = chunk[:frames]
    except asyncio.QueueEmpty:
        outdata[:] = 0

audio_stream = sd.OutputStream(
    device=speaker_index,
    samplerate=AUDIO_RATE,
    channels=AUDIO_CHANNELS,
    dtype='float32',
    blocksize=BLOCKSIZE,
    callback=audio_callback
)
audio_stream.start()

async def handler(ws):
    print(f"Client connected: {ws.remote_address}")
    try:
        async for data in ws:
            if data.startswith("MIC:"):
                audio_bytes = base64.b64decode(data[4:])
                audio_array = np.frombuffer(audio_bytes, dtype=np.float32).reshape(-1, AUDIO_CHANNELS)

                # Apply gain
                # GAIN = 1.5
                # GAIN = 5.0
                GAIN = 3.0
                audio_array = np.clip(audio_array * GAIN, -1.0, 1.0)

                # Keep queue very short to reduce latency
                while audio_buffer.qsize() > 1:
                    _ = await audio_buffer.get()

                await audio_buffer.put(audio_array)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {ws.remote_address}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None):
        print(f"Streaming server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()

asyncio.run(main())
