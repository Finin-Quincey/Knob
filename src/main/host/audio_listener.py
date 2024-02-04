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
import logging as log

from constants import *
from serial_manager import SerialManager
from media_manager import MediaManager
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
        log.info("Initialising audio listener")
        
        self.frequency_resolution = AUDIO_SAMPLE_RATE / AUDIO_SAMPLES_PER_FRAME
        # Controls how the contribution of previous samples decays over time
        self.window_weights = np.array([np.linspace(0, 1, AUDIO_AVERAGING_WINDOW)]).transpose()
        # Logarithmic frequency bins (20Hz - 4kHz seems pretty good)
        self.frequency_bins = [(2 * 10**n) for n in np.linspace(1, 3.3, SPECTRUM_FREQUENCY_BINS + 1)]

        self.sample_frequencies = np.fft.rfftfreq(AUDIO_SAMPLES_PER_FRAME * ROLLING_FRAMES, 1/AUDIO_SAMPLE_RATE)
        # Quantise transform frequencies into bins
        self.freq_bin_indices = np.digitize(self.sample_frequencies, self.frequency_bins)

        # Init arrays
        self.prev_samples = np.zeros([AUDIO_SAMPLES_PER_FRAME * ROLLING_FRAMES, 2])
        self.prev_hist_data = np.zeros((AUDIO_AVERAGING_WINDOW, SPECTRUM_FREQUENCY_BINS))

        # Blank variables for later
        self.mic = None
        self.rec = None

    
    def __enter__(self):
        pass # Mic gets opened later


    def __exit__(self, exc_type, exc_value, traceback):
        # Finalise everything when the program exits for whatever reason
        self._finalise_recorder(exc_type, exc_value, traceback)


    def _finalise_recorder(self, exc_type = None, exc_value = None, traceback = None):
        """
        Manually calls __exit__ on the mic recorder
        """
        if self.rec is not None:
            try:
                self.rec.__exit__(exc_type, exc_value, traceback)
            except RuntimeError:
                self.rec = None # Delete the recorder object if it errors


    def check_mic_change(self):
        """
        Checks whether the default speakers have changed, and if so, sets the new speakers' loopback as the new microphone
        """
        speaker_id = sc.default_speaker().id

        if self.mic is None or self.mic.id != speaker_id:
            # Get the loopback mic for the default (i.e. current) speakers
            self.mic = sc.get_microphone(speaker_id, include_loopback = True)
            log.info("Microphone updated to %s", self.mic)
            self._finalise_recorder() # Manually exit recorder before reinitialising
            self.rec = self.mic.recorder(samplerate = 48000)
            self.rec.__enter__()

        
    def update(self, serial_manager: SerialManager, media_manager: MediaManager):
        """
        Called from the main program loop to update the audio listener
        """
        self.check_mic_change()

        if self.rec is None: return

        try:
            data = self.rec.record(numframes = 1024)
        except RuntimeError as e:
            log.log(TRACE, "Unable to record audio (error code %s)", e)
            return
        
        ### Simple VU Meter ###
        
        # left = min(float(np.max(data[:, 0])) * 5.0, 1)
        # right = min(float(np.max(data[:, 1])) * 5.0, 1)

        # serial_manager.send(msp.VUMessage(left, right))

        ### Spectrum Analyser ###

        self.prev_samples = np.row_stack([self.prev_samples[AUDIO_SAMPLES_PER_FRAME:, :], data])

        mono = np.max(self.prev_samples, axis = 1)
        amps = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) # Apply Hanning window before FFT to combat spectral leakage

        amps_binned = np.array([np.max(amps[np.where(self.freq_bin_indices == i+1)]) for i in range(SPECTRUM_FREQUENCY_BINS)])
        amps_binned = np.nan_to_num(amps_binned)

        # Shift prev samples up 1, discard the oldest and append the current sample
        self.prev_hist_data = np.row_stack([self.prev_hist_data[1:, :], amps_binned])
        # Calculate average across frames
        freq_avg = np.sum(self.prev_hist_data * self.window_weights, axis = 0) / sum(self.window_weights)

        freq_normalised = [min(0.02 * v / media_manager.get_volume(True), 1) for v in freq_avg] # Normalise to 0-1 range

        serial_manager.send(msp.SpectrumMessage(freq_normalised, freq_normalised))