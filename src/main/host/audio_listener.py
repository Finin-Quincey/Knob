"""
Audio Listener

Module responsible for listening to the system output audio and processing it into the form required by the device.
Automatically checks for changes to the default speaker and updates the mic accordingly.
"""
# In future the plan is to do FFTs and such like in this class. Although it would certainly be possible to send raw
# audio to the device, that will require much higher bandwidth to get anything usable, so any performance gained by
# not having to do maths on the host end will most likely be offset by having to send a ton of serial data... I think

import soundcard as sc
import numpy as np
import sys
import logging as log

from serial_manager import SerialManager
import message_protocol as msp

# Using context managers in modules that are part of a wider update cycle brings up an interesting problem: when a
# resource (a microphone in this case) needs to be acquired by a module and retained across update cycles, control
# flow needs to pass between the 'child' module and the 'parent' module within the same context (i.e. without
# releasing the acquired resources). As far as I can tell, the best way to do this is to make the 'child' module
# into a singleton class which is itself a context manager, then call the __enter__ and __exit__ methods of the
# original context manager manually as required (seems a bit wrong to call dunder methods directly but it works
# okay). This makes sense really, since an exception might occur in the parent module and we still need to release
# the resources acquired by the child module.

# Discussion here:
# https://stackoverflow.com/questions/24235083/how-to-delegate-management-of-child-context-to-parent

class AudioListener():
    """
    Audio Listener

    Class responsible for listening to the system output audio and processing it into the form required by the device.
    Automatically checks for changes to the default speaker and updates the mic accordingly.
    """

    def __init__(self):
        """
        Creates a new audio listener
        """
        self.mic = None
        self.rec = None

    
    def __enter__(self):
        pass # Mic gets opened later


    def __exit__(self, exc_type, exc_value, traceback):
        # Finalise everything when the program exits for whatever reason
        if self.rec is not None:
            self.rec.__exit__(exc_type, exc_value, traceback) # Finalise recorder context manager manually


    def check_mic_change(self):
        """
        Checks whether the default speakers have changed, and if so, sets the new speakers' loopback as the new microphone
        """
        speaker_id = sc.default_speaker().id

        if self.mic is None or self.mic.id != speaker_id:
            # Get the loopback mic for the default (i.e. current) speakers
            self.mic = sc.get_microphone(speaker_id, include_loopback = True)
            log.info("Microphone updated to %s", self.mic)
            if self.rec is not None: self.rec.__exit__(None, None, None)
            self.rec = self.mic.recorder(samplerate = 48000)
            self.rec.__enter__()

        
    def update(self, serial_manager: SerialManager):
        """
        Called from the main program loop to update the audio listener
        """
        self.check_mic_change()

        if self.rec is None: return

        data = self.rec.record(numframes = 1024)
        left = min(float(np.max(data[:, 0])) * 5.0, 1)
        right = min(float(np.max(data[:, 1])) * 5.0, 1)

        serial_manager.send(msp.VUMessage(left, right))