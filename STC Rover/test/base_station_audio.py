import serial
import numpy as np
import sounddevice as sd
import threading
from collections import deque

PORT = "COM7"
BAUD = 921600
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1024
CHUNK_BYTES = CHUNK_SAMPLES * 4  # 4 bytes per int32 sample

# High-pass filter constant
HPF_ALPHA = 0.995

# Fixed gain
GAIN = 1.0 / 50000.0

ser = serial.Serial(PORT, BAUD)

# Jitter buffer (stores several chunks)
audio_queue = deque(maxlen=10)

def serial_reader():
    """ Continuously read from ESP32 and push audio chunks into jitter buffer. """
    prev_sample = 0

    while True:
        raw = ser.read(CHUNK_BYTES)
        samples = np.frombuffer(raw, dtype=np.int32)

        # Shift 24-bit left-justified INMP441 data
        samples = samples >> 14

        # High-pass filter (removes DC + rumble)
        filtered = np.zeros_like(samples, dtype=np.float32)
        filtered[0] = samples[0] - prev_sample
        for i in range(1, len(samples)):
            filtered[i] = HPF_ALPHA * (filtered[i-1] + samples[i] - samples[i-1])
        prev_sample = samples[-1]

        # Apply fixed gain
        audio = filtered * GAIN

        # Clip to safe range
        audio = np.clip(audio, -1.0, 1.0)

        # Add to jitter buffer
        audio_queue.append(audio)

def audio_callback(outdata, frames, time, status):
    """ Fills speaker buffer with latest audio chunk. """
    if len(audio_queue) > 0:
        chunk = audio_queue.popleft()
        outdata[:] = chunk.reshape(-1, 1)
    else:
        # No data yet — output silence
        outdata[:] = np.zeros((frames, 1), dtype=np.float32)

threading.Thread(target=serial_reader, daemon=True).start()

with sd.OutputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    callback=audio_callback,
    blocksize=CHUNK_SAMPLES
):
    print("Streaming live audio (Ctrl+C to stop)")
    while True:
        pass