import asyncio
import websockets
import signal
import sys
import RPi.GPIO as GPIO
import time

start_time = time.time()
last_command_time = time.time()
TIMEOUT = 0.75

IN1, IN2, IN3, IN4 = 23, 24, 27, 22
ENA, ENB = 18, 19

GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
GPIO.setup([ENA, ENB], GPIO.OUT)

pwmA = GPIO.PWM(ENA, 20000)
pwmB = GPIO.PWM(ENB, 20000)
pwmA.start(0)
pwmB.start(0)

async def handler(websocket):
    global start_time, last_command_time
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            if isinstance(message, bytes) and len(message) == 5:
                opcode, motor_number, power, pwm, direction = message

                last_command_time = time.time()

                # elapsed_time = time.time() - start_time
                # print(f'Time since last motor code: {elapsed_time} seconds')
                # start_time = time.time()

                print(f"Opcode: {opcode}, Motor: {motor_number}, Power: {power}, PWM: {pwm}, Direction: {direction}")
                if pwm < 50:
                    if not motor_number:
                        pwmA.ChangeDutyCycle(0)
                    else:
                        pwmB.ChangeDutyCycle(0)
                else:
                    duty = pwm * 100 / 255
                    if not motor_number:
                        GPIO.output(IN1, GPIO.LOW if direction else GPIO.HIGH)
                        GPIO.output(IN2, GPIO.HIGH if direction else GPIO.LOW)
                        pwmA.ChangeDutyCycle(duty)
                    else:
                        GPIO.output(IN3, GPIO.HIGH if direction else GPIO.LOW)
                        GPIO.output(IN4, GPIO.LOW if direction else GPIO.HIGH)
                        pwmB.ChangeDutyCycle(duty)
            else:
                print(f"Received raw message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def watchdog():
    global last_command_time
    while True:
        if time.time() - last_command_time > TIMEOUT:
            pwmA.ChangeDutyCycle(0)
            pwmB.ChangeDutyCycle(0)
        await asyncio.sleep(0.1)

async def main():
    asyncio.create_task(watchdog())
    async with websockets.serve(handler, "0.0.0.0", 8081):
        print("WebSocket server running on ws://0.0.0.0:8081")
        await asyncio.Future()  # run forever

def cleanup():
    print("Cleaning up GPIO and cancelling tasks...")
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()

def handle_exit(signum, frame):
    for task in asyncio.all_tasks(loop):
        task.cancel()
    cleanup()
    sys.exit(0)

# Signal handling
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except asyncio.CancelledError:
    pass
finally:
    cleanup()