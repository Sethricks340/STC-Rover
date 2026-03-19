# TODO: find camera dynamically


# This error if can't find it: (not plugged in)
# [ERROR:0@54.131] global obsensor_uvc_stream_channel.cpp:163 getStreamChannelGroup Camera index out of range
# Cannot open camera
# [ WARN:0@56.337] global cap_v4l.cpp:914 open VIDEOIO(V4L2:/dev/video0): can't open camera by index
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] Not a video capture device.
# [video4linux2,v4l2 @ 0x30be1c60] ioctl(VIDIOC_G_INPUT): Inappropriate ioctl for device


import cv2
import asyncio
import websockets
import base64
import sounddevice as sd

TAILSCALE_IP = "100.94.206.108"  # Sender Pi Tailscale IP
PORT = 8765

# Audio settings
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_BLOCKSIZE = 1024

# Select devices
# TODO: find camera dynamically
mic_index = 1  # Replace with index of Logitech C270 mic from sd.query_devices()
camera_index = 0  # Usually 0 for the first USB camera

async def send_camera_audio(websocket):
    # global video_start_time, audio_start_time
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 15)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    audio_queue = asyncio.Queue()

    # Audio callback
    def audio_callback(indata, frames, time_info, status):
        # global audio_start_time
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
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
                jpg_text = base64.b64encode(buffer).decode('utf-8')
                await websocket.send(f"VID:{jpg_text}")

            # Send audio if available
            while not audio_queue.empty():
                audio_bytes = await audio_queue.get()
                audio_text = base64.b64encode(audio_bytes).decode('utf-8')
                await websocket.send(f"AUD:{audio_text}")

            await asyncio.sleep(0.2)
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