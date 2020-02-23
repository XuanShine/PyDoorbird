try:
    import RPi.GPIO as GPIO
except ImportError:
    from RPiSim.GPIO import GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

# gpio_buzzer = 7

def buzz(gpio_buzzer=7):
    GPIO.setup(gpio_buzzer, GPIO.OUT)
    for _ in range(6):
        GPIO.output(gpio_buzzer, GPIO.HIGH)
        sleep(0.5)
        GPIO.output(gpio_buzzer, GPIO.LOW)
        sleep(0.5)

if __name__ == "__main__":
    buzz()
