import utime
import math
from neopixel import Neopixel
import machine
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
    return (-i + PIXEL_OFFSET) % PIXEL_COUNT
    
# Inverse of the above
def to_pos_index(i):
    return (-i - PIXEL_OFFSET) % PIXEL_COUNT

def update_ring(ring):
    """
    Wrapper for ring.show() that disables interrupts while it executes
    """
    # Sending data to the NeoPixels is timing critical, therefore it MUST NOT be interrupted or the LED drivers
    # will interpret the incomplete data, resulting in the wrong pixels turning on
    state = machine.disable_irq()
    ring.show()
    machine.enable_irq(state)

def show_fraction(ring, fraction, rgb):
    if fraction < 0 or fraction > 1: raise ValueError("Fraction must be between 0 and 1 (inclusive)")
    ring.clear()
    f = fraction * PIXEL_COUNT
    on_pixels = int(f)
    remainder = f - on_pixels
    for i in range(on_pixels):
        # v = (i/PIXEL_COUNT) / fraction
        # ring.set_pixel(to_pixel_index(i), [int(c * v) for c in rgb])
        ring.set_pixel(to_pixel_index(i), rgb)
    ring.set_pixel(to_pixel_index(on_pixels), [int(c * remainder) for c in rgb])

    # for i in range(PIXEL_COUNT):
    #     brightness = 1 if to_pos_index(i) == on_pixels else (1 if to_pos_index(i) < on_pixels else 0)
    #     ring.set_pixel(i, [int(c * brightness) for c in rgb])

    update_ring(ring)

### Pin Setup ###

led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

ring = Neopixel(PIXEL_COUNT, 0, PIXEL_DATA_PIN, "GRB")

encoder_a_pin = Pin(ENCODER_A_PIN, Pin.IN, Pin.PULL_UP)
encoder_b_pin = Pin(ENCODER_B_PIN, Pin.IN, Pin.PULL_UP)
encoder_last_pulse_pin = encoder_a_pin
encoder_last_pulse_val = 0

encoder_sw_pin = Pin(ENCODER_SW_PIN, Pin.IN, Pin.PULL_UP)

def handle_encoder_pulse(pin):

    pin_val = pin.value() # Capture value of the tiggered pin as soon as possible in case it changes

    global encoder_count
    global encoder_a_pin
    global encoder_b_pin
    global encoder_last_pulse_pin
    global encoder_last_pulse_val
    #global encoder_cooldown

    is_b_pin = pin is encoder_b_pin
    other_pin_val = encoder_a_pin.value() if is_b_pin else encoder_b_pin.value()

    # Basic debouncing
    # ignore = encoder_cooldown > 0
    # if ignore: return
    # encoder_cooldown = 1

    if encoder_last_pulse_pin is pin and encoder_last_pulse_val == pin_val: return # Ignore if the same pin was pulsed twice

    encoder_last_pulse_pin = pin # Update last pulsed pin
    encoder_last_pulse_val = pin_val

    delta = 1 if is_b_pin == (pin_val == other_pin_val) else -1
    encoder_count = (encoder_count + delta) % ENCODER_COUNTS_PER_REV
    print(encoder_count)

encoder_a_pin.irq(handle_encoder_pulse, Pin.IRQ_RISING | Pin.IRQ_FALLING)
encoder_b_pin.irq(handle_encoder_pulse, Pin.IRQ_RISING | Pin.IRQ_FALLING)

prev_encoder_count = 0

while True:
    if encoder_cooldown > 0: encoder_cooldown -= 1
    # if encoder_count != prev_encoder_count:
    #     prev_encoder_count = encoder_count
    f = encoder_count / ENCODER_COUNTS_PER_REV
    show_fraction(ring, f, ring.colorHSV(int(((80 - f * 180 + encoder_sw_pin.value() * 180) % 360) / 360 * 65535), 150, 10))
    #led_pin.value(not encoder_sw_pin.value())
    utime.sleep_ms(20)