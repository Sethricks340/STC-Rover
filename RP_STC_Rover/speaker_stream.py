import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd

TAILSCALE_IP = "100.94.206.108"
MIC_PORT = 8766

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_BLOCKSIZE = 1024

# Output device (change name if needed)
speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:  # your USB speaker name
        speaker_index = i
        break
if speaker_index is None:
    speaker_index = sd.default.device[1]  # fallback default output

async def receive_mic():
    while True:
        try:
            uri = f"ws://{TAILSCALE_IP}:{MIC_PORT}"
            async with websockets.connect(uri) as websocket:
                print(f"Connected to microphone stream at {uri}")

                stream = sd.OutputStream(device=speaker_index,
                                         samplerate=AUDIO_RATE,
                                         channels=AUDIO_CHANNELS,
                                         blocksize=AUDIO_BLOCKSIZE)
                stream.start()

                while True:
                    data = await websocket.recv()
                    if data.startswith("MIC:"):
                        audio_bytes = base64.b64decode(data[4:])
                        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                        audio_array = np.clip(audio_array * 3.0, -1.0, 1.0)
                        stream.write(audio_array)
        except (ConnectionRefusedError, OSError, websockets.exceptions.ConnectionClosed):
            print("Connection lost, retrying in 2 seconds...")
            await asyncio.sleep(2)

asyncio.run(receive_mic())