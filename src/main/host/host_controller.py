"""
Host Controller

Module responsible for overall control flow on the host end. Runs on host process start.
"""

import audio_manager as audio

import message_protocol as msp
from host_serial_manager import HostSerialManager


### Setup ###

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


# Register message handlers
serial_manager.register_handler(msp.VolumeRequestMessage, handle_vol_request)
serial_manager.register_handler(msp.VolumeMessage, handle_vol_change)


### Main Program Loop ###

with serial_manager:

    while(True):

        serial_manager.update()