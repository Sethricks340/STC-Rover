import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np
import threading

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
CHUNK_SIZE = 1024
MIC_PORT = 8766
ROBOT_TAILSCALE_IP = "100.94.206.108"
SERVER_URI = f"ws://{ROBOT_TAILSCALE_IP}:{MIC_PORT}"

async def stream_microphone():
    async with websockets.connect(SERVER_URI) as websocket:
        print("Connected to server")

        # Use a thread-safe queue to send audio from callback to async websocket
        audio_queue = asyncio.Queue()

        def callback(indata, frames, time_info, status):
            audio_bytes = indata.astype(np.float32).tobytes()
            audio_queue.put_nowait(audio_bytes)
            print("Sending audio chunk:", len(audio_bytes), "bytes")  

        with sd.InputStream(channels=AUDIO_CHANNELS,
                            samplerate=AUDIO_RATE,
                            blocksize=CHUNK_SIZE,
                            callback=callback):
            print("Streaming microphone...")
            while True:
                audio_bytes = await audio_queue.get()
                msg = base64.b64encode(audio_bytes).decode('ascii')
                await websocket.send(msg)

asyncio.run(stream_microphone())