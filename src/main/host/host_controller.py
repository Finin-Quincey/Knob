"""
Host Controller

Module responsible for overall control flow on the host end. Runs on host process start.
"""

import os
import sys
import time
from enum import Enum
import logging as log
from serial.serialutil import SerialException

from constants import *
import message_protocol as msp
from host_serial_manager import HostSerialManager
from audio_listener import AudioListener
from media_manager import MediaManager
from spotify_hooks import SpotifyHooks

### Constants ###

# No-op placeholder function to avoid null-checking of variables of function type
NOOP = lambda: None # TODO: potentially have this accept self as an arg?

class ExitFlag(Enum):
    NONE        = 0
    RESTART     = 1
    EXIT        = 2
    DEV_MODE    = 3

class Event(Enum):
    DEVICE_CONNECT      = "device_connect"
    DEVICE_DISCONNECT   = "device_disconnect"
    PLAY                = "play"
    PAUSE               = "pause"
    SPOTIFY_CONNECT     = "spotify_connect"
    SPOTIFY_DISCONNECT  = "spotify_disconnect"


def init_logger():
    
    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)

    console_log_handler = log.StreamHandler(sys.stderr)
    primary_log_handler = log.FileHandler(os.path.join(LOGS_DIRECTORY, PRIMARY_LOG_FILENAME), mode = "w")
    debug_log_handler = log.FileHandler(os.path.join(LOGS_DIRECTORY, DEBUG_LOG_FILENAME), mode = "w")

    console_log_handler.setLevel(log.DEBUG)
    primary_log_handler.setLevel(log.INFO)
    debug_log_handler.setLevel(TRACE)

    log.basicConfig(format = "%(asctime)s [%(levelname)s] %(message)s",
                    datefmt = "%d-%m-%Y %I:%M:%S %p",
                    level = log.DEBUG,
                    handlers = [console_log_handler, primary_log_handler, debug_log_handler])

    log.addLevelName(TRACE, 'TRACE') # TRACE logging level for repetitive messages


class HostController:

    def __init__(self) -> None:

        init_logger()

        log.info("*** Starting volume knob host process ***")

        self.exit_flag = ExitFlag.NONE

        # Event callback registry
        self.event_callbacks = {e: NOOP for e in Event}

        # Init other modules/classes
        self.serial_manager = HostSerialManager()
        self.audio_listener = AudioListener()
        self.media_manager = MediaManager()
        self.spotify_hooks = SpotifyHooks()

        # Register message handlers
        log.info("Registering message handlers")
        self.serial_manager.register_handler(msp.VolumeRequestMessage,   self.handle_vol_request_msg)
        self.serial_manager.register_handler(msp.VolumeMessage,          self.handle_vol_change_msg)
        self.serial_manager.register_handler(msp.TogglePlaybackMessage,  self.handle_toggle_playback_msg)
        self.serial_manager.register_handler(msp.SkipMessage,            self.handle_skip_msg)
        self.serial_manager.register_handler(msp.LikeMessage,            self.handle_like_msg)


    def set_callback(self, event: Event, callback):
        """
        Attaches the given callback function to the specified event. This will overwrite any existing
        callback for that event.
        
        #### Parameters
        ##### Required
        - `event`: The event to attach the callback to.
        - `callback`: The function to run each time the given event happens.
        """
        self.event_callbacks[event] = callback

    
    def _post_event(self, event):
        """
        [Internal] Triggers the callback associated with the given event, if any.
        """
        self.event_callbacks[event]()
        

    ### Handlers ###

    def handle_vol_request_msg(self, msg: msp.VolumeRequestMessage):
        # Get current system volume
        vol = self.media_manager.get_volume()
        # Construct a volume message and send it to the device
        reply = msp.VolumeMessage(vol)
        self.serial_manager.send(reply)


    def handle_vol_change_msg(self, msg: msp.VolumeMessage):
        # Set system volume to new level
        self.media_manager.set_volume(msg.volume)


    def handle_toggle_playback_msg(self, msg: msp.TogglePlaybackMessage):
        self.media_manager.toggle_playback()
        # Not currently sending a reply since we're using the same animation for play and pause
        if self.media_manager.is_playing():
            self._post_event(Event.PLAY)
        else:
            self._post_event(Event.PAUSE)


    def handle_skip_msg(self, msg: msp.SkipMessage):
        self.media_manager.skip(msg.forward)


    def handle_like_msg(self, msg: msp.LikeMessage):
        # Spotify takes a short time to respond so it's easier to reply first with the opposite of the
        # previous liked status and then do the actual toggling
        reply = msp.LikeStatusMessage(not self.spotify_hooks.is_current_song_liked())
        self.spotify_hooks.toggle_liked_status()
        self.serial_manager.send(reply)


    ### Program Control Functions ###

    def restart(self):
        """
        Restarts both the host and device programs.
        """
        log.info("Initiating host process restart...")
        self.exit_flag = ExitFlag.RESTART

    
    def exit(self):
        """
        Exits the host program and restarts the device program ready to reconnect once the host is relaunched.
        """
        log.info("Initiating host process exit...")
        self.exit_flag = ExitFlag.EXIT


    def dev_mode(self):
        """
        Exits both the host and device programs, returning the device to the REPL to allow reprogramming.
        """
        log.info("Initiating host process exit...")
        self.exit_flag = ExitFlag.DEV_MODE


    ### Main Program Loop ###

    def run(self):

        while(self.exit_flag == ExitFlag.NONE):

            log.info("Attempting device connection...")

            try:

                with self.serial_manager:

                    self._post_event(Event.DEVICE_CONNECT)
                    log.info("Device connection successful")

                    while(self.exit_flag == ExitFlag.NONE):

                        self.serial_manager.update()
                        self.audio_listener.update(self.serial_manager, self.media_manager)

                    if self.exit_flag == ExitFlag.DEV_MODE:
                        log.info("Putting device into development mode...")
                        self.serial_manager.send(msp.ExitMessage())
                    else:
                        log.info("Sending device restart...")
                        self.serial_manager.send(msp.DisconnectMessage())

                    time.sleep(0.02)

            except SerialException:
                log.info(f"Failed to connect to device; retrying in {RECONNECT_DELAY} seconds")
                
            self._post_event(Event.DEVICE_DISCONNECT)

            time.sleep(RECONNECT_DELAY)

        log.debug("Host controller exit (exit flag: %s)", self.exit_flag)
        log.info("*** Stopping volume knob host process ***")

        # Cleanup
        log.shutdown()

        return self.exit_flag