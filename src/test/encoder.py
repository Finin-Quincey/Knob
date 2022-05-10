import utime
import math
from neopixel import Neopixel
from machine import Pin
import micropython

micropython.alloc_emergency_exception_buf(100) # Recommended when using interrupts

### Constants ###

ONBOARD_LED_PIN = 25
PIXEL_DATA_PIN = 28
ENCODER_A_PIN = 22
ENCODER_B_PIN = 21
ENCODER_SW_PIN = 18
ENCODER_COUNTS_PER_REV = 20 * 4

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

### Globals ###

encoder_count = 0
encoder_cooldown = 0

### Functions ###

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

### Pin Setup ###

led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

ring = Neopixel(PIXEL_COUNT, 0, PIXEL_DATA_PIN, "GRB")

encoder_a_pin = Pin(ENCODER_A_PIN, Pin.IN, Pin.PULL_UP)
encoder_b_pin = Pin(ENCODER_B_PIN, Pin.IN, Pin.PULL_UP)

encoder_sw_pin = Pin(ENCODER_SW_PIN, Pin.IN, Pin.PULL_UP)

def handle_encoder_pulse(pin):

    global encoder_count
    global encoder_a_pin
    global encoder_b_pin
    global encoder_cooldown

    # Basic debouncing
    ignore = encoder_cooldown > 0
    encoder_cooldown = 1
    #if ignore: return

    led_pin.toggle()

    delta = 1 if (pin is encoder_b_pin) == (encoder_a_pin.value() == encoder_b_pin.value()) else -1
    encoder_count = (encoder_count + delta) % ENCODER_COUNTS_PER_REV

encoder_a_pin.irq(handle_encoder_pulse, Pin.IRQ_RISING | Pin.IRQ_FALLING)

while True:
    if encoder_cooldown > 0: encoder_cooldown -= 1
    f = encoder_count / ENCODER_COUNTS_PER_REV
    show_fraction(ring, f, ring.colorHSV(int(((80 - f * 180 + encoder_sw_pin.value() * 180) % 360) / 360 * 65535), 150, 10))
    #led_pin.value(not encoder_sw_pin.value())
    utime.sleep_ms(20)