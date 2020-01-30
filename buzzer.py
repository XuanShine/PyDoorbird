import RPi.GPIO as GPIO
from time import sleep

GPIO.setwarnings(False)
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
    main()
