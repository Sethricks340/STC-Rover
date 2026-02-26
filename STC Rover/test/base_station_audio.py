# TODO: static background noise, delay, choppy

import websocket
import numpy as np
import sounddevice as sd
import threading
from collections import deque
import time

WS_URL = "ws://stc_esp.local:81/audio"

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1024
HPF_ALPHA = 0.9
GAIN = 1.0 / 50000.0

audio_queue = deque(maxlen=20)

def ws_reader():
    prev_sample = 0

    ws = websocket.WebSocket()
    ws.connect(WS_URL)
    print("WebSocket connected")

    while True:
        try:
            raw = ws.recv() # receive binary frame
            if len(raw) == 0:
                continue

            # raw = ws.recv()
            print("bytes:", len(raw))

            samples = np.frombuffer(raw, dtype=np.int32)
            print("samples:", len(samples),
                "min:", samples.min() if len(samples) else None,
                "max:", samples.max() if len(samples) else None)

            if len(samples) == 0:
                continue

            samples = samples >> 14  # shift INMP441 data to account for header

            filtered = np.zeros_like(samples, dtype=np.float32)
            filtered[0] = samples[0] - prev_sample

            for i in range(1, len(samples)):
                filtered[i] = HPF_ALPHA * (filtered[i-1] + samples[i] - samples[i-1])

            prev_sample = samples[-1]

            # audio = np.clip(filtered * GAIN, -1.0, 1.0)
            # audio_queue.append(audio)

            # audio = samples.astype(np.float32) / 2**21
            # audio_queue.append(np.clip(audio, -1.0, 1.0))

            audio = samples.astype(np.float32)
            audio /= (np.max(np.abs(audio)) + 1e-9)
            audio *= 0.8   # loud
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