"""
Media Manager

Contains functions for interacting with the system volume and playback controls.
"""

import time
import asyncio
import logging as log
from constants import *

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as WinSessionManager

### Constants ###

# Playback statuses
CLOSED = 0
OPENED = 1
CHANGING = 2
STOPPED = 3
PLAYING = 4
PAUSED = 5


class MediaManager:

    def __init__(self) -> None:
        """
        Initialises a new instance of the media manager.
        """
        log.info("Initialising media manager")
        self.audio_device_id = "" # Audio device UUID string, used to check for device changes
        self._update_audio_device() # Init system volume access with pycaw

    
    def _update_audio_device(self):
        """
        [Internal] Checks for changes to the audio output device and updates the connection if necessary.
        """
        t = time.perf_counter()
        device = AudioUtilities.GetSpeakers()
        id = device.GetId()
        if id != self.audio_device_id: # If audio output device changed
            self.audio_device_id = id # Store the new device UUID
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.system_volume = cast(interface, POINTER(IAudioEndpointVolume))
            log.log(TRACE, f"Audio device interface retrieval took {time.perf_counter() - t:.3f}s")
            log.info("Audio output device updated")


    def get_volume(self, suppress_log = False) -> float:
        """
        Returns the system volume, expressed as a fraction between 0 (muted) and 1 (max volume)
        """
        if not suppress_log: log.log(TRACE, "Attempting to get system volume")
        self._update_audio_device()
        return self.system_volume.GetMasterVolumeLevelScalar() # type: ignore


    def set_volume(self, volume: float):
        """
        Sets the system volume to the given value, specified as a fraction between 0 (muted) and 1 (max volume)
        """
        log.debug("Attempting to set volume to %.2f", volume)
        if volume < 0 or volume > 1: raise ValueError(f"Invalid volume level: {volume}")
        self._update_audio_device()
        self.system_volume.SetMasterVolumeLevelScalar(volume, None) # type: ignore


    def is_playing(self) -> bool:
        """
        Returns True if there is media currently playing, False otherwise
        """
        log.log(TRACE, "Attempting to retrieve current playback status")
        return _run_with_timer(_is_playing)


    def toggle_playback(self) -> bool:
        """
        Attempts to toggle the playback of the current media
        """
        log.debug("Attempting to toggle playback")
        return _run_with_timer(_toggle_playback)


    def skip(self, forward = True) -> bool:
        """
        Attempts to skip to the next (default) or previous track and returns True if successful
        """
        log.debug("Attempting to skip %s", "forawrd" if forward else "backward")
        if forward: return _run_with_timer(_skip_forward)
        else: return _run_with_timer(_skip_backward)


    def get_media_info(self) -> dict:
        """
        Returns a dictionary of information about the currently-playing media
        """
        log.log(TRACE, "Attempting to retrieve info for the current media")
        return _run_with_timer(_get_media_info)


### Internal Functions ###

def _run_with_timer(func):
    t = time.perf_counter()
    result = asyncio.run(func())
    log.log(TRACE, f"{func.__name__}() took {time.perf_counter() - t:.3f}s")
    return result


async def _is_playing() -> bool:
    """
    [Internal] Attempts to retrieve the playback status of the current media, returning True if there is currently media
    playing and False otherwise
    """
    sessions = await WinSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        pbinfo = current_session.get_playback_info() # No await because this isn't async
        return pbinfo.playback_status == PLAYING #type:ignore

    return False # Can't be any media playing if there's no session!


async def _toggle_playback() -> bool:
    """
    [Internal] Attempts to toggle the playback status of the current media and returns True if successful
    """
    # FIXME:
    # Exception has occurred: OSError
    # [WinError -2147418110] Call was canceled by the message filter
    sessions = await WinSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_toggle_play_pause_async()
        return success

    return False
    #raise Exception('No playback session currently running')


async def _skip_forward() -> bool:
    """
    [Internal] Attempts to skip to the next track and returns True if successful
    """
    sessions = await WinSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_skip_next_async()
        return success

    return False
    #raise Exception('No playback session currently running')


async def _skip_backward() -> bool:
    """
    [Internal] Attempts to skip to the previous track and returns True if successful
    """
    sessions = await WinSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_skip_previous_async()
        return success

    return False
    #raise Exception('No playback session currently running')


async def _get_media_info():
    """
    [Internal] Retrieves information about the currently-playing media and returns it as a dictionary. Returns an empty
    dictionary if there is no playback session running.
    """
    sessions = await WinSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:

        info = await current_session.try_get_media_properties_async()
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
        info_dict['genres'] = list(info_dict['genres'])

        return info_dict

    return {}
    #raise Exception('No playback session currently running')