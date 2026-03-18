# import cv2
# import asyncio
# import websockets
# import base64
# import numpy as np
# import sounddevice as sd

# TAILSCALE_IP = "100.94.206.108"  # Sender Pi Tailscale IP
# PORT = 8766

# # Audio settings
# AUDIO_RATE = 48000
# AUDIO_CHANNELS = 1
# AUDIO_BLOCKSIZE = 1024

# # Select devices
# mic_index = 1  # Replace with index of Logitech C270 mic from sd.query_devices()
# camera_index = 0  # Usually 0 for the first USB camera

# async def send_camera_audio(websocket):
#     cap = cv2.VideoCapture(camera_index)
#     if not cap.isOpened():
#         print("Cannot open camera")
#         return

#     audio_queue = asyncio.Queue()

#     # Audio callback
#     def audio_callback(indata, frames, time, status):
#         audio_queue.put_nowait(indata.copy().tobytes())

#     # Start audio input stream (mic)
#     stream = sd.InputStream(device=mic_index,
#                             samplerate=AUDIO_RATE,
#                             channels=AUDIO_CHANNELS,
#                             blocksize=AUDIO_BLOCKSIZE,
#                             callback=audio_callback)
#     stream.start()

#     try:
#         while True:
#             # Send video
#             ret, frame = cap.read()
#             if ret:
#                 _, buffer = cv2.imencode('.jpg', frame)
#                 jpg_text = base64.b64encode(buffer).decode('utf-8')
#                 await websocket.send(f"VID:{jpg_text}")

#             # Send audio if available
#             while not audio_queue.empty():
#                 audio_bytes = await audio_queue.get()
#                 audio_text = base64.b64encode(audio_bytes).decode('utf-8')
#                 await websocket.send(f"AUD:{audio_text}")

#             await asyncio.sleep(0.01)
#     except websockets.exceptions.ConnectionClosed:
#         print("Client disconnected")
#     finally:
#         cap.release()
#         stream.stop()
#         stream.close()

# async def main():
#     async with websockets.serve(send_camera_audio, "0.0.0.0", PORT):
#         print(f"Camera + audio server running on ws://{TAILSCALE_IP}:{PORT}")
#         await asyncio.Future()  # run forever

# asyncio.run(main())



# import sounddevice as sd
# import numpy as np

# AUDIO_RATE = 48000
# AUDIO_CHANNELS = 1
# DURATION = 5  # seconds

# print("Recording 5 seconds from default mic...")
# recording = sd.rec(int(DURATION * AUDIO_RATE),
#                    samplerate=AUDIO_RATE,
#                    channels=AUDIO_CHANNELS,
#                    dtype='float32')  # default device
# sd.wait()

# print("Playback...")
# sd.play(recording, samplerate=AUDIO_RATE)
# sd.wait()
# print("Done")


 
import asyncio
import websockets
import base64
import sounddevice as sd

PI_IP = "100.94.206.108"
PORT = 8766
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
BLOCKSIZE = 1024

async def stream_audio():
    audio_queue = asyncio.Queue()

    def audio_callback(indata, frames, time, status):
        audio_queue.put_nowait(indata.copy().tobytes())

    stream = sd.InputStream(
        samplerate=AUDIO_RATE,
        channels=AUDIO_CHANNELS,
        blocksize=BLOCKSIZE,
        callback=audio_callback
    )
    stream.start()

    async with websockets.connect(f"ws://{PI_IP}:{PORT}") as ws:
        print(f"Connected to Pi at ws://{PI_IP}:{PORT}")
        try:
            while True:
                audio_bytes = await audio_queue.get()
                audio_text = base64.b64encode(audio_bytes).decode('utf-8')
                await ws.send(f"MIC:{audio_text}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        finally:
            stream.stop()
            stream.close()

asyncio.run(stream_audio())