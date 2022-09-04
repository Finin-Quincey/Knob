"""
Host Controller

Module responsible for overall control flow on the host end. Runs on host process start.
"""

import time
import logging as log

from constants import *
import audio_manager as audio
import message_protocol as msp
from host_serial_manager import HostSerialManager
from serial.serialutil import SerialException


### Setup ###

log.basicConfig(format = "%(asctime)s [%(levelname)s] %(message)s",
                datefmt = "%d-%m-%Y %I:%M:%S %p",
                level = log.DEBUG)

log.addLevelName(TRACE, 'TRACE') # TRACE logging level for repetitive messages

log.info("*** Starting volume knob host process ***")

serial_manager = HostSerialManager()

audio.init()


### Handlers ###

def handle_vol_request(msg: msp.VolumeRequestMessage):
    # Get current system volume
    vol = audio.get_volume()
    # Construct a volume message and send it to the device
    reply = msp.VolumeMessage(vol)
    serial_manager.send(reply)


def handle_vol_change(msg: msp.VolumeMessage):
    # Set system volume to new level
    audio.set_volume(msg.volume)


def handle_toggle_playback(msg: msp.TogglePlaybackMessage):
    audio.toggle_playback()
    # TODO: Retrieve playback status and send to device


def handle_skip_message(msg: msp.SkipMessage):
    audio.skip(msg.forward)


# Register message handlers
log.info("Registering message handlers")
serial_manager.register_handler(msp.VolumeRequestMessage, handle_vol_request)
serial_manager.register_handler(msp.VolumeMessage, handle_vol_change)
serial_manager.register_handler(msp.TogglePlaybackMessage, handle_toggle_playback)
serial_manager.register_handler(msp.SkipMessage, handle_skip_message)


### Main Program Loop ###

while(True):

    log.info("Attempting device connection...")

    try:

        with serial_manager:

            log.info("Device connection successful")

            while(True):

                serial_manager.update()

                time.sleep(0.02)

    except SerialException:
        log.info(f"Failed to connect to device; retrying in {RECONNECT_DELAY} seconds")

    time.sleep(RECONNECT_DELAY)