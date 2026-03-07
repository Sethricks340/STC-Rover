import cv2
import asyncio
import websockets
import base64

TAILSCALE_IP = "100.94.206.108"  # Robot Pi Tailscale IP
PORT = 8765

# Top-level handler with exactly two arguments
# async def send_camera(websocket, path):
async def send_camera(websocket):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            await websocket.send(jpg_as_text)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        cap.release()

# Main server entry
async def main():
    async with websockets.serve(send_camera, "0.0.0.0", PORT):
        print(f"Camera server running on ws://{TAILSCALE_IP}:{PORT}")
        await asyncio.Future()  # keep running forever

# Run the server
asyncio.run(main())