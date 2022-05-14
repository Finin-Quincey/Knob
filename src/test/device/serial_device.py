import sys
import utime
from machine import Pin

ONBOARD_LED_PIN = 25

led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

while True:
    ch = sys.stdin.read(4)
    if str(ch) == 'Ping':
        led_pin.toggle()
        sys.stdout.write(b'Pong')
    #sys.stdout.write(ch) # Send it back
    utime.sleep_ms(20)