import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
CHUNK_SIZE = 1024  # samples per chunk
MIC_PORT = 8766  # different from your camera/audio port
ROBOT_TAILSCALE_IP = "100.94.206.108"
SERVER_URI = f"ws://{ROBOT_TAILSCALE_IP}:{MIC_PORT}"

async def stream_microphone():
    async with websockets.connect(SERVER_URI) as websocket:
        def callback(indata, frames, time, status):
            audio_array = indata.astype(np.float32)
            audio_bytes = audio_array.tobytes()
            msg = "MIC:" + base64.b64encode(audio_bytes).decode('ascii')
            # Send async safely
            asyncio.run_coroutine_threadsafe(websocket.send(msg), asyncio.get_event_loop())

        with sd.InputStream(channels=AUDIO_CHANNELS,
                            samplerate=AUDIO_RATE,
                            blocksize=CHUNK_SIZE,
                            callback=callback):
            print("Streaming mic to port", MIC_PORT)
            while True:
                await asyncio.sleep(1)

asyncio.run(stream_microphone())