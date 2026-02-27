#TODO: keeps disconnecting. 

import websocket
import numpy as np
import sounddevice as sd
import threading
from collections import deque
import time

# WS_URL = "ws://stc_esp.local:81/audio"  # For home Wifi
WS_URL = "ws://10.15.44.90:81/audio"   # For byui Wifi

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1024
# HPF_ALPHA = 0.9
HPF_ALPHA = 0.995
GAIN = 1.0 / 5000.0

audio_queue = deque(maxlen=20)

def ws_reader():
    prev_sample = 0
    ws = websocket.WebSocket()
    ws.connect(WS_URL)
    print("WebSocket connected")

    buffer = bytearray()  # accumulate incoming bytes

    while True:
        try:
            raw = ws.recv()
            if not raw:
                continue

            buffer.extend(raw)  # add incoming bytes

            # Process full chunks only
            while len(buffer) >= CHUNK_SAMPLES * 4:  # 4 bytes per int32
                chunk_bytes = buffer[:CHUNK_SAMPLES*4]
                buffer = buffer[CHUNK_SAMPLES*4:]

                samples = np.frombuffer(chunk_bytes, dtype=np.int32)
                samples = samples >> 14  # shift INMP441 data

                filtered = np.zeros_like(samples, dtype=np.float32)
                filtered[0] = samples[0] - prev_sample
                for i in range(1, len(samples)):
                    filtered[i] = HPF_ALPHA * (filtered[i-1] + samples[i] - samples[i-1])
                prev_sample = samples[-1]

                audio = filtered * GAIN
                audio = np.clip(audio, -1.0, 1.0)
                audio_queue.append(audio)

        except websocket.WebSocketConnectionClosedException:
            print("WebSocket closed, reconnecting...")
            time.sleep(0.5)
            ws = websocket.WebSocket()
            ws.connect(WS_URL)

def audio_callback(outdata, frames, time, status):
    if len(audio_queue) > 0:
        chunk = audio_queue.popleft()
        outdata[:] = chunk[:frames].reshape(-1, 1)
    else:
        outdata[:] = np.zeros((frames, 1), dtype=np.float32)

threading.Thread(target=ws_reader, daemon=True).start()

with sd.OutputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    callback=audio_callback,
    blocksize=CHUNK_SAMPLES
):
    print("Streaming WiFi audio (Ctrl+C to stop)")
    while True:
        pass