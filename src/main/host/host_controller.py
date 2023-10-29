"""
Host Controller

Module responsible for overall control flow on the host end. Runs on host process start.
"""

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


# No-op placeholder function to avoid null-checking of variables of function type
NOOP = lambda: None # TODO: potentially have this accept self as an arg?

### Setup ###

log.basicConfig(format = "%(asctime)s [%(levelname)s] %(message)s",
                datefmt = "%d-%m-%Y %I:%M:%S %p",
                level = log.DEBUG)

log.addLevelName(TRACE, 'TRACE') # TRACE logging level for repetitive messages


class ExitFlag(Enum):
    NONE = 0
    RESTART = 1
    EXIT = 2


class HostController:

    def __init__(self) -> None:

        self.exit_flag = ExitFlag.NONE

        # Event callbacks
        self.connect_callback = NOOP
        self.disconnect_callback = NOOP

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
        log.info("Sending device restart...")
        self.serial_manager.send(msp.DisconnectMessage())
        log.info("Restarting host process...")
        self.exit_flag = ExitFlag.RESTART

    
    def exit(self):
        """
        Exits the host program and restarts the device program ready to reconnect once the host is relaunched.
        """
        log.info("Sending device restart...")
        self.serial_manager.send(msp.DisconnectMessage())
        log.info("Exiting host process...")
        self.exit_flag = ExitFlag.EXIT


    def dev_mode(self):
        """
        Exits both the host and device programs, returning the device to the REPL to allow reprogramming.
        """
        log.info("Putting device into development mode...")
        self.serial_manager.send(msp.ExitMessage())
        log.info("Exiting host process...")
        self.exit_flag = ExitFlag.EXIT


    ### Main Program Loop ###

    def run(self):

        while(self.exit_flag == ExitFlag.NONE):

            log.info("Attempting device connection...")

            try:

                with self.serial_manager:

                    self.connect_callback()
                    log.info("Device connection successful")

                    while(self.exit_flag == ExitFlag.NONE):

                        self.serial_manager.update()
                        self.audio_listener.update(self.serial_manager, self.media_manager)

                        time.sleep(0.02)

            except SerialException:
                log.info(f"Failed to connect to device; retrying in {RECONNECT_DELAY} seconds")
                
            self.disconnect_callback()

            time.sleep(RECONNECT_DELAY)

        return self.exit_flag