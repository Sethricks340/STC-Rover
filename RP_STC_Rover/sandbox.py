# TODO:
# GPIO outputs to motor driver based off of inputs
    # turn off it loose connection?
# USB Camera/Microphone
# USB Speaker

import asyncio
import websockets

import RPi.GPIO as GPIO

IN1 = 23
IN2 = 24
IN3 = 27
IN4 = 22

ENA = 18
ENB = 19

GPIO.setmode(GPIO.BCM)

GPIO.setup([IN1,IN2,IN3,IN4], GPIO.OUT)
GPIO.setup([ENA,ENB], GPIO.OUT)

pwmA = GPIO.PWM(ENA, 20000)
pwmB = GPIO.PWM(ENB, 20000)

pwmA.start(0)
pwmB.start(0)

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            # Ensure we have a binary message of length 5
            if isinstance(message, bytes) and len(message) == 5:
                opcode, motor_number, power, pwm, direction = message
                print(f"Opcode: {opcode}, Motor: {motor_number}, "
                      f"Power: {power}, PWM: {pwm}, Direction: {direction}")
                
                if (pwm < 30):
                    pwmA.ChangeDutyCycle(0)
                    pwmB.ChangeDutyCycle(0)

                else:
                    # Motor A (IN1, IN2)
                    GPIO.output(IN1, GPIO.LOW if direction else GPIO.HIGH)
                    GPIO.output(IN2, GPIO.HIGH if direction else GPIO.LOW)

                    # Motor B (IN3, IN4) — invert direction to match motor A
                    GPIO.output(IN3, GPIO.HIGH if direction else GPIO.LOW)  
                    GPIO.output(IN4, GPIO.LOW if direction else GPIO.HIGH)  

                    duty = pwm * 100 / 255
                    pwmA.ChangeDutyCycle(duty)
                    pwmB.ChangeDutyCycle(duty)

            else:
                print(f"Received raw message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8081):
        print("WebSocket server running on ws://0.0.0.0:8081")
        await asyncio.Future()  # run forever

asyncio.run(main())