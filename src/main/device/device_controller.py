"""
Device Controller

Responsible for overall control flow on the device end. This file is run on device boot.
"""

from machine import Pin
import utime
import micropython
import sys

import led_ring
import device_serial_manager as dsm
import message_protocol as msp

### Constants ###

ONBOARD_LED_PIN = 25
PIXEL_DATA_PIN = 28
ENCODER_A_PIN = 22
ENCODER_B_PIN = 21
ENCODER_SW_PIN = 18
ENCODER_PPR = 20

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

EXCEPTIONS = [
    AssertionError,
    AttributeError,
    ImportError,
    IndexError,
    KeyboardInterrupt,
    KeyError,
    MemoryError,
    NameError,
    NotImplementedError,
    OSError,
    StopIteration,
    SyntaxError,
    SystemExit,
    TypeError,
    ValueError,
    ZeroDivisionError
]

### Handlers ###

def handle_volume_msg(msg: msp.VolumeMessage):
    ring.set_colour((msg.volume, 255, 255))
    utime.sleep(2)

### Main Program Loop ###

def run_loop():
    h = 0
    while True:
        dsm.update(ring)
        utime.sleep_ms(20)
        ring.set_colour((180, 200, h))
        h = (h + 1) % 256

### Startup ###

sw_pin = Pin(ENCODER_SW_PIN, Pin.IN, Pin.PULL_UP)
led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

# Get-out function: plug in while holding encoder button
if sw_pin.value() == 0:
    micropython.kbd_intr(3) # Re-enable interrupts, just in case
    # Flash onboard LED to indicate successful entry into reprogramming mode
    for _ in range(5):
        utime.sleep_ms(200)
        led_pin.toggle()
    sys.exit() # Exit the program immediately and return to the REPL

# Need this or the USB serial stream will interrupt when a 3 is sent
# Note that this effectively disables the REPL, making it impossible to interact with the pico!
# Therefore there should always be some kind of 'get-out' function (see above)
micropython.kbd_intr(-1)

#########################

### Setup ###
# This should probably be in a function but for now I'm just putting it here

ring = led_ring.LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)

dsm.init()
dsm.register_handler(msp.VolumeMessage, handle_volume_msg)

try:
    run_loop()

except Exception as e:
    print(e)
    ring.set_colour((50, 255, 255))
    utime.sleep(1)
    for i, ex_type in enumerate(EXCEPTIONS):
        if isinstance(e, ex_type):
            ring.display_bytes(bytes([i]))
            break