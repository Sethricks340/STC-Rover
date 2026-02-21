import serial
import numpy as np
from scipy.io.wavfile import write

# Serial setup
ser = serial.Serial('COM7', 921600)

# Parameters
sample_rate = 16000       # same as ESP32
num_samples = 16000 * 5   # record 5 seconds

# Read raw data
raw_data = bytearray()
while len(raw_data) < num_samples * 4:  # 4 bytes per sample
    raw_data += ser.read(4096)

# Convert bytes to 32-bit signed integers
audio_samples = np.frombuffer(raw_data, dtype=np.int32)

# Normalize to 16-bit PCM
audio_16bit = np.int16(audio_samples / (2**31) * 32767)

# Save as WAV
write("mic_recording.wav", sample_rate, audio_16bit)

print("Saved mic_recording.wav! Play it with any audio player.")