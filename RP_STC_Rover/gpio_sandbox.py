import RPi.GPIO as GPIO
import time

IN1 = 23
IN2 = 24
IN3 = 27
IN4 = 22

ENA = 18
ENB = 19

GPIO.setmode(GPIO.BCM)

GPIO.setup([IN1,IN2,IN3,IN4], GPIO.OUT)
GPIO.setup([ENA,ENB], GPIO.OUT)

pwmA = GPIO.PWM(ENA, 1000)
pwmB = GPIO.PWM(ENB, 1000)

pwmA.start(0)
pwmB.start(0)

direction = 1

GPIO.output(IN1, GPIO.LOW if direction else GPIO.HIGH)
GPIO.output(IN2, GPIO.HIGH if direction else GPIO.LOW)

GPIO.output(IN3, GPIO.LOW if direction else GPIO.HIGH)
GPIO.output(IN4, GPIO.HIGH if direction else GPIO.LOW)

pwm = 255
duty = pwm * 100 / 255
pwmA.ChangeDutyCycle(duty)
pwmB.ChangeDutyCycle(duty)

time.sleep(5)

pwmA.stop()
pwmB.stop()
GPIO.cleanup()
