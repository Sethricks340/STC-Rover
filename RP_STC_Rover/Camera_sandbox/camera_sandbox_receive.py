# import cv2
# import asyncio
# import websockets
# import base64
# import numpy as np

# ROBOT_TAILSCALE_IP = "100.94.206.108"
# PORT = 8765

# async def receive_camera():
#     uri = f"ws://{ROBOT_TAILSCALE_IP}:{PORT}"
#     while True:  # keep trying to connect
#         try:
#             async with websockets.connect(uri) as websocket:
#                 print("Connected to camera server")
#                 while True:
#                     jpg_as_text = await websocket.recv()
#                     jpg_original = base64.b64decode(jpg_as_text)
#                     nparr = np.frombuffer(jpg_original, np.uint8)
#                     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#                     cv2.imshow("Robot Camera", frame)
#                     if cv2.waitKey(1) & 0xFF == ord('q'):
#                         return
#         except (ConnectionRefusedError, OSError):
#             print("Camera server not available, retrying in 2 seconds...")
#             await asyncio.sleep(2)
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed, reconnecting in 2 seconds...")
#             await asyncio.sleep(2)

# asyncio.run(receive_camera())




import cv2
import asyncio
import websockets
import base64
import numpy as np
import sounddevice as sd

ROBOT_TAILSCALE_IP = "100.94.206.108"  # Sender Pi IP
PORT = 8765

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1

# Select audio output device
speaker_index = 1  # Replace with index of Jieli device from sd.query_devices()

async def receive_camera_audio():
    uri = f"ws://{ROBOT_TAILSCALE_IP}:{PORT}"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to camera+audio server")

                # Start audio output stream
                audio_stream = sd.OutputStream(device=speaker_index,
                                               samplerate=AUDIO_RATE,
                                               channels=AUDIO_CHANNELS)
                audio_stream.start()

                while True:
                    data = await websocket.recv()
                    if data.startswith("VID:"):
                        jpg_original = base64.b64decode(data[4:])
                        nparr = np.frombuffer(jpg_original, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        cv2.imshow("Robot Camera", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            return
                    # elif data.startswith("AUD:"):
                    #     audio_bytes = base64.b64decode(data[4:])
                    #     audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                    #     audio_stream.write(audio_array)
                    # Assume everything received here is raw audio bytes
                    audio_bytes = await websocket.recv()
                    audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                    audio_stream.write(audio_array)
        except (ConnectionRefusedError, OSError):
            print("Server not available, retrying in 2s...")
            await asyncio.sleep(2)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, reconnecting in 2s...")
            await asyncio.sleep(2)

asyncio.run(receive_camera_audio())