"""
Device Controller

Responsible for overall control flow on the device end. This file is run on device boot.
"""

from machine import Pin
import utime
import micropython
import sys

import led_ring
import rotary_encoder
import device_serial_manager as dsm
import message_protocol as msp
import state_machine

### Constants ###

ONBOARD_LED_PIN = 25
PIXEL_DATA_PIN = 28
ENCODER_A_PIN = 22
ENCODER_B_PIN = 21
ENCODER_SW_PIN = 18
ENCODER_PPR = 20

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

VOL_DISPLAY_HOLD_TIME = 2000 # Time in ms after the knob stops turning that the volume will continue being displayed
LIKE_HOLD_TIME = 2000 # Time in ms that the button must be held for in order to like/unlike a song
SKIP_COUNT_THRESHOLD = 5 # Number of counts (80 being a full circle) the knob must be rotated whilst pressed to skip a track

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
    leds.set_colour((msg.volume, 255, 255))
    utime.sleep(2)

### Main Program Loop ###

def run_loop():

    while True:
        
        dsm.update()
        leds.update()
        state_machine.update()

        utime.sleep_ms(20)

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

leds = led_ring.LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)
encoder = rotary_encoder.Encoder(ENCODER_A_PIN, ENCODER_B_PIN, ENCODER_SW_PIN, ENCODER_PPR)

dsm.init()
dsm.register_handler(msp.VolumeMessage, handle_volume_msg)

try:
    run_loop()

except Exception as e:
    print(e)
    leds.set_colour((50, 255, 255))
    utime.sleep(1)
    for i, ex_type in enumerate(EXCEPTIONS):
        if isinstance(e, ex_type):
            leds.display_bytes(bytes([i]))
            break