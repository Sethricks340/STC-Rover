import sounddevice as sd

samplerate = 44100
duration = 5  # seconds

print("Recording...")
audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
sd.wait()

print("Playing...")
sd.play(audio, samplerate)
sd.wait()