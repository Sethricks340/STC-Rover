import serial
import numpy as np
import sounddevice as sd
import time

SERIAL_PORT = "COM7"
BAUDRATE = 115200
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024  # samples per callback

ser = serial.Serial(SERIAL_PORT, BAUDRATE)

def audio_callback(outdata, frames, time_info, status):
    raw = ser.read(CHUNK_SIZE * 4)  # 4 bytes per int32 sample
    audio = np.frombuffer(raw, dtype=np.int32)
    audio = audio.astype(np.float32) / 2147483648.0  # normalize
    outdata[:] = audio.reshape(-1, 1)

with sd.OutputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype='float32',
    callback=audio_callback,
    blocksize=CHUNK_SIZE
):
    print("Streaming audio from ESP32...")
    try:
        while True:
            time.sleep(0.1)  # keep main thread alive
    except KeyboardInterrupt:
        print("Stopped streaming")