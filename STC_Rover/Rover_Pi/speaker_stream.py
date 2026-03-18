# # TODO:
# #   Run on reboot 

# # ---- To be run on car (Pi) ---- 

# import asyncio
# import websockets
# import signal
# import sys
# import base64
# import numpy as np
# import sounddevice as sd

# PORT = 8766
# AUDIO_RATE = 48000
# AUDIO_CHANNELS = 1
# BLOCKSIZE = 1024  # match or smaller than Windows blocksize

# # Find your speaker
# speaker_index = None
# for i, dev in enumerate(sd.query_devices()):
#     if "UACDemoV1.0" in dev['name']:
#         speaker_index = i
#         print("Connected to UACDemoV1 speaker")
#         break
# if speaker_index is None:
#     print("USB speaker not found, using default output")
#     speaker_index = sd.default.device[1]

# # Async queue to hold incoming audio
# audio_buffer = asyncio.Queue()

# # OutputStream callback pulls audio from the queue continuously
# def audio_callback(outdata, frames, time, status):
#     try:
#         chunk = audio_buffer.get_nowait()
#         if len(chunk) < frames:
#             outdata[:len(chunk)] = chunk
#             outdata[len(chunk):] = 0  # pad with zeros
#         else:
#             outdata[:] = chunk[:frames]
#     except asyncio.QueueEmpty:
#         outdata[:] = 0  # silence if nothing in queue

# audio_stream = sd.OutputStream(
#     device=speaker_index,
#     samplerate=AUDIO_RATE,
#     channels=AUDIO_CHANNELS,
#     dtype='float32',
#     blocksize=BLOCKSIZE,
#     callback=audio_callback
# )
# audio_stream.start()

# # WebSocket handler
# async def handler(websocket):
#     print(f"Client connected: {websocket.remote_address}")
#     try:
#         async for data in websocket:
#             if isinstance(data, str) and data.startswith("MIC:"):
#                 audio_bytes = base64.b64decode(data[4:])
#                 audio_array = np.frombuffer(audio_bytes, dtype=np.float32).reshape(-1, AUDIO_CHANNELS)
#                 # Put into queue for callback to play
#                 await audio_buffer.put(audio_array)
#             else:
#                 print(f"Received raw message: {data}")
#     except websockets.exceptions.ConnectionClosed:
#         print(f"Client disconnected: {websocket.remote_address}")

# # Run server
# async def main():
#     async with websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None):
#         print(f"WebSocket server running on ws://0.0.0.0:{PORT}")
#         await asyncio.Future()  # run forever

# # Cleanup for exit
# def cleanup():
#     print("Stopping audio stream and cleaning up...")
#     audio_stream.stop()
#     audio_stream.close()

# def handle_exit(signum, frame):
#     for task in asyncio.all_tasks():
#         task.cancel()
#     cleanup()
#     sys.exit(0)

# signal.signal(signal.SIGINT, handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         cleanup()



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