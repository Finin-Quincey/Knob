import led_ring

### Constants ###

ONBOARD_LED_PIN = 25
PIXEL_DATA_PIN = 28
ENCODER_A_PIN = 22
ENCODER_B_PIN = 21
ENCODER_SW_PIN = 18
ENCODER_PPR = 20

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

from machine import Pin
import utime

led_pin = Pin(25, Pin.OUT)
p = Pin(0, Pin.OUT)

led_pin.value(1)

ring = led_ring.LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)

h = 0

while True:
    utime.sleep_ms(20)
    ring.set_colour((180, 200, h))
    h = (h + 1) % 256