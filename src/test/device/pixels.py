import utime
import math
from neopixel import Neopixel
from machine import Pin

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

PIXEL_DATA_PIN = 28

def to_pixel_index(i):
    return (PIXEL_OFFSET - i) % PIXEL_COUNT

def show_fraction(ring, fraction, rgb):
    #if fraction < 0 or fraction > 1: raise ValueError("Fraction must be between 0 and 1 (inclusive)")
    ring.clear()
    f = fraction * PIXEL_COUNT
    on_pixels = int(f)
    remainder = f - on_pixels
    for i in range(on_pixels):
        # v = (i/PIXEL_COUNT) / fraction
        # ring.set_pixel(to_pixel_index(i), [int(c * v) for c in rgb])
        ring.set_pixel(to_pixel_index(i), rgb)
    ring.set_pixel(to_pixel_index(on_pixels), [int(c * remainder) for c in rgb])
    ring.show()

led_pin = Pin(25, Pin.OUT)

led_pin.high()

ring = Neopixel(24, 0, PIXEL_DATA_PIN, "GRB")

# for i in range(PIXEL_COUNT):
#     ring.set_pixel(i, ring.colorHSV(int(i/PIXEL_COUNT * 65535), 255, 20))
# ring.show()

while True:
    f = (math.sin((utime.ticks_ms() / 2000)) + 1) / 2
    show_fraction(ring, f, ring.colorHSV(int((260 - f * 180) / 360 * 65535), 150, 10))
    #utime.sleep_ms(20)