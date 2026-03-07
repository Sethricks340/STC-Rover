import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pin = 18
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, 1000)   # 1000 Hz
pwm.start(50)               # 50% duty cycle

time.sleep(5)

pwm.ChangeDutyCycle(75)

pwm.stop()
GPIO.cleanup()