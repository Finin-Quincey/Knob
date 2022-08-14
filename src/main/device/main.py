"""
main.py

Device code entry point. Also handles onboard LED indicator and switching to reprogramming mode.
"""

from machine import Pin
import utime
import micropython
import sys

from constants import * # Usually considered bad practice but here I think it improves readability

### Initialisation ###

# This is done in here, BEFORE importing any modules that might error, so we always have some idea of what's going on

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

del sw_pin # Remove switch pin object, we're done with it

######################

try:
    # This import must be done AFTER the get-out function
    import device_controller
    device_controller.run()

except Exception as e:
    # Flash forever if an error happened before we even got to the main loop
    while True:
        print(e) # Having trouble reading this so let's repeat it forever
        led_pin.toggle()
        utime.sleep_ms(200)