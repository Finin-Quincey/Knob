"""
Device Controller

Module responsible for overall control flow on the device end. The run() function is called from main.py on device boot.
"""

import utime

from constants import * # Usually considered bad practice but here I think it improves readability

from led_ring import LedRing
from rotary_encoder import Encoder

### Setup ###

# Hardware
leds = LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)
encoder = Encoder(ENCODER_A_PIN, ENCODER_B_PIN, ENCODER_SW_PIN, ENCODER_PPR)

from device_serial_manager import DeviceSerialManager
import message_protocol as msp
import state_machine

# Serial manager
serial_manager = DeviceSerialManager()


def init():
    serial_manager.register_handler(msp.VolumeMessage, handle_volume_msg)
    serial_manager.register_handler(msp.VUMessage, handle_vu_msg)
    serial_manager.register_handler(msp.SpectrumMessage, handle_spectrum_msg)
    serial_manager.register_handler(msp.LikeStatusMessage, handle_like_status_msg)


### Handlers ###

def handle_volume_msg(msg: msp.VolumeMessage):
    leds.crossfade(200)
    state_machine.set_state(state_machine.VolumeAdjustState(msg.volume))


def handle_vu_msg(msg: msp.VUMessage):
    if state_machine.get_current_state().should_display_audio():
        leds.set_colour((240 - int(msg.left * 100), 255 - int(msg.left * 230), 200 + int(msg.left * 55)))


def handle_spectrum_msg(msg: msp.SpectrumMessage):
    if state_machine.get_current_state().should_display_audio():
        for i, v in enumerate(msg.left):
            leds.set_pixel(PIXEL_COUNT-i-1, (280 - i * 14 - int(v * 100), 255 - int(v * 180), 190 + int(v * 65)))
        for i, v in enumerate(msg.right):
            leds.set_pixel(i+1,             (280 - i * 14 - int(v * 100), 255 - int(v * 180), 190 + int(v * 65)))


def handle_like_status_msg(msg: msp.LikeStatusMessage):
    if state_machine.is_in_state(state_machine.PressedState):
        leds.set_colour(LIKE_COLOUR if msg.liked else UNLIKE_COLOUR)
        leds.crossfade(LED_TRANSITION_DURATION)


### Main Program Loop ###

def run():

    try:
        init()
        while True:
            update_loop()

    except Exception as e:
        leds.set_colour((0, 255, 255))
        leds.update()
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

    utime.sleep_ms(40)