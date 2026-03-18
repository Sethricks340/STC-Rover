import asyncio
import websockets
import base64
import sounddevice as sd

PI_IP = "100.94.206.108"  # Pi Tailscale IP
PORT = 8766
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
BLOCKSIZE = 1024

async def send_audio():
    audio_queue = asyncio.Queue()

    # Audio callback puts mic data into queue
    def audio_callback(indata, frames, time, status):
        audio_queue.put_nowait(indata.copy().tobytes())

    stream = sd.InputStream(
        samplerate=AUDIO_RATE,
        channels=AUDIO_CHANNELS,
        blocksize=BLOCKSIZE,
        dtype='int16',
        callback=audio_callback
    )
    stream.start()

    async with websockets.connect(f"ws://{PI_IP}:{PORT}") as ws:
        print(f"Connected to Pi at ws://{PI_IP}:{PORT}")
        while True:
            if not audio_queue.empty():
                audio_bytes = await audio_queue.get()
                audio_text = base64.b64encode(audio_bytes).decode('utf-8')
                await ws.send(f"MIC:{audio_text}")
            else:
                await asyncio.sleep(0.005)  # small sleep to avoid busy loop

asyncio.run(send_audio())