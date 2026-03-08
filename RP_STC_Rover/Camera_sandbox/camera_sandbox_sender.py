# import cv2
# import asyncio
# import websockets
# import base64

# TAILSCALE_IP = "100.94.206.108"  # Robot Pi Tailscale IP
# PORT = 8765

# # Top-level handler with exactly two arguments
# # async def send_camera(websocket, path):
# async def send_camera(websocket):
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("Cannot open camera")
#         return
#     try:
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 continue
#             _, buffer = cv2.imencode('.jpg', frame)
#             jpg_as_text = base64.b64encode(buffer).decode('utf-8')
#             await websocket.send(jpg_as_text)
#     except websockets.exceptions.ConnectionClosed:
#         print("Client disconnected")
#     finally:
#         cap.release()

# # Main server entry
# async def main():
#     async with websockets.serve(send_camera, "0.0.0.0", PORT):
#         print(f"Camera server running on ws://{TAILSCALE_IP}:{PORT}")
#         await asyncio.Future()  # keep running forever

# # Run the server
# asyncio.run(main())



import cv2
import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd

TAILSCALE_IP = "100.94.206.108"  # Sender Pi Tailscale IP
PORT = 8765

# Audio settings
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_BLOCKSIZE = 1024

# Select devices
mic_index = 1  # Replace with index of Logitech C270 mic from sd.query_devices()
camera_index = 0  # Usually 0 for the first USB camera

async def send_camera_audio(websocket):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    audio_queue = asyncio.Queue()

    # Audio callback
    def audio_callback(indata, frames, time, status):
        audio_queue.put_nowait(indata.copy().tobytes())

    # Start audio input stream (mic)
    stream = sd.InputStream(device=mic_index,
                            samplerate=AUDIO_RATE,
                            channels=AUDIO_CHANNELS,
                            blocksize=AUDIO_BLOCKSIZE,
                            callback=audio_callback)
    stream.start()

    try:
        while True:
            # Send video
            ret, frame = cap.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                jpg_text = base64.b64encode(buffer).decode('utf-8')
                await websocket.send(f"VID:{jpg_text}")

            # Send audio if available
            while not audio_queue.empty():
                audio_bytes = await audio_queue.get()
                audio_text = base64.b64encode(audio_bytes).decode('utf-8')
                await websocket.send(f"AUD:{audio_text}")

            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        cap.release()
        stream.stop()
        stream.close()

async def main():
    async with websockets.serve(send_camera_audio, "0.0.0.0", PORT):
        print(f"Camera + audio server running on ws://{TAILSCALE_IP}:{PORT}")
        await asyncio.Future()  # run forever

asyncio.run(main())