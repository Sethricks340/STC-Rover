import asyncio
import websockets
import cv2
import base64
import RPi.GPIO as GPIO

# Camera setup
TAILSCALE_IP = "100.94.206.108"
CAM_PORT = 8765

# Motor setup
MOTOR_PORT = 8081
IN1, IN2, IN3, IN4 = 23, 24, 27, 22
ENA, ENB = 18, 19

GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
GPIO.setup([ENA, ENB], GPIO.OUT)
pwmA = GPIO.PWM(ENA, 20000)
pwmB = GPIO.PWM(ENB, 20000)
pwmA.start(0)
pwmB.start(0)

# Camera server
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
        print("Camera client disconnected")
    finally:
        cap.release()

# Motor server
async def handle_motor(websocket):
    print(f"Motor client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            if isinstance(message, bytes) and len(message) == 5:
                opcode, motor_number, power, pwm, direction = message
                duty = pwm * 100 / 255
                if pwm < 50:
                    pwmA.ChangeDutyCycle(0)
                    pwmB.ChangeDutyCycle(0)
                else:
                    GPIO.output(IN1, GPIO.LOW if direction else GPIO.HIGH)
                    GPIO.output(IN2, GPIO.HIGH if direction else GPIO.LOW)
                    GPIO.output(IN3, GPIO.HIGH if direction else GPIO.LOW)
                    GPIO.output(IN4, GPIO.LOW if direction else GPIO.HIGH)
                    pwmA.ChangeDutyCycle(duty)
                    pwmB.ChangeDutyCycle(duty)
    except websockets.exceptions.ConnectionClosed:
        print(f"Motor client disconnected: {websocket.remote_address}")

# Run both servers concurrently
async def main():
    cam_server = websockets.serve(send_camera, "0.0.0.0", CAM_PORT)
    motor_server = websockets.serve(handle_motor, "0.0.0.0", MOTOR_PORT)
    await asyncio.gather(cam_server, motor_server)
    
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
    loop.run_forever()
finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()