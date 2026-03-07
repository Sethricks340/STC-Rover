import cv2
import asyncio
import websockets
import base64
import numpy as np

ROBOT_TAILSCALE_IP = "100.94.206.108"  # Robot Pi Tailscale IP
PORT = 8765

async def receive_camera():
    uri = f"ws://{ROBOT_TAILSCALE_IP}:{PORT}"
    async with websockets.connect(uri) as websocket:
        while True:
            jpg_as_text = await websocket.recv()
            jpg_original = base64.b64decode(jpg_as_text)
            nparr = np.frombuffer(jpg_original, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imshow("Robot Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

asyncio.get_event_loop().run_until_complete(receive_camera())