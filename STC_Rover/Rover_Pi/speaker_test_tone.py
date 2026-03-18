import sounddevice as sd
import numpy as np

AUDIO_RATE = 48000
DURATION = 3  # seconds
FREQ = 440  # A4

# Replace with your USB speaker index on Pi
speaker_index = None
for i, dev in enumerate(sd.query_devices()):
    if "UACDemoV1.0" in dev['name']:
        speaker_index = i
        print(f"Found USB speaker at index {i}")
        break
if speaker_index is None:
    raise RuntimeError("USB speaker not found")

t = np.linspace(0, DURATION, int(AUDIO_RATE * DURATION), endpoint=False)
tone = 0.5 * np.sin(2 * np.pi * FREQ * t).astype(np.float32)

print("Playing test tone on USB speaker...")
sd.play(tone, samplerate=AUDIO_RATE, device=speaker_index)
sd.wait()
print("Done")