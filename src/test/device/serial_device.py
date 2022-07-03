import sys
import utime
import uselect
from machine import Pin

ONBOARD_LED_PIN = 25

led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

stdin_poll = uselect.poll()
# Not sure why pylance doesn't like the following line
stdin_poll.register(sys.stdin, uselect.POLLIN)  # type: ignore

def read():
    return sys.stdin.readline() if stdin_poll.poll(0) else None

while True:
    ch = read() # sys.stdin.readline()
    if ch and 'Ping' in str(ch):
        led_pin.toggle()
        sys.stdout.write(b'Pong')
    #sys.stdout.write(ch) # Send it back
    utime.sleep_ms(200)
    led_pin.toggle()
    utime.sleep_ms(200)
    led_pin.toggle()
    utime.sleep(1)