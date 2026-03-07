# # TODO: 
# # camera is an AV device. Stream this over to the other pi. 
# # note: do this on public wifi, as it might block some of this traffic


# import cv2

# # 0 = first USB camera
# cap = cv2.VideoCapture(0)

# if not cap.isOpened():
#     print("Cannot open camera")
#     exit()

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame")
#         break

#     cv2.imshow("USB Camera", frame)

#     # Press 'q' to quit
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()


import cv2
import asyncio
import websockets
import base64

TAILSCALE_IP = "100.94.206.108"  # Robot Pi Tailscale IP
PORT = 8765

async def send_camera(websocket, path):
    cap = cv2.VideoCapture(0)  # USB camera
    if not cap.isOpened():
        print("Cannot open camera")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        await websocket.send(jpg_as_text)

start_server = websockets.serve(send_camera, "0.0.0.0", PORT)
print(f"Camera server running on ws://{TAILSCALE_IP}:{PORT}")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()