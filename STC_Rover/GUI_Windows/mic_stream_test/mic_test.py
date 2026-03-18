import sounddevice as sd
import numpy as np

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
DURATION = 5  # seconds

print("Recording 5 seconds from default mic...")
recording = sd.rec(int(DURATION * AUDIO_RATE),
                   samplerate=AUDIO_RATE,
                   channels=AUDIO_CHANNELS,
                   dtype='float32')  # default device
sd.wait()

print("Playback...")
sd.play(recording, samplerate=AUDIO_RATE)
sd.wait()
print("Done")