"""
Device Controller

Module responsible for overall control flow on the device end. The run() function is called from main.py on device boot.
"""

import utime

from constants import * # Usually considered bad practice but here I think it improves readability

from led_ring import LedRing
from rotary_encoder import Encoder
from device_serial_manager import DeviceSerialManager
import message_protocol as msp
import state_machine

### Setup ###

# Hardware
leds = LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)
encoder = Encoder(ENCODER_A_PIN, ENCODER_B_PIN, ENCODER_SW_PIN, ENCODER_PPR)

# Serial manager
serial_manager = DeviceSerialManager()


def init():
    serial_manager.register_handler(msp.VolumeMessage, handle_volume_msg)


### Handlers ###

def handle_volume_msg(msg: msp.VolumeMessage):
    leds.set_colour((msg.volume, 255, 255))
    utime.sleep(2)


### Main Program Loop ###

def run():

    try:
        init()
        while True:
            update_loop()

    except Exception as e:
        leds.set_colour((0, 255, 255))
        utime.sleep(1)
        for i, ex_type in enumerate(EXCEPTIONS):
            if isinstance(e, ex_type):
                leds.display_bytes(bytes([i]))
                # Re-throw the error so main.py will catch it in an infinite loop rather than dumping out to the REPL
                # That way the serial output won't get flushed and we can actually read the error description
                raise e


def update_loop():
        
    serial_manager.update()
    leds.update()
    state_machine.update()

    utime.sleep_ms(20)