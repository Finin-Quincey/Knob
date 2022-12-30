"""
Media Manager

Contains functions for interacting with the system volume and playback controls.
"""

import asyncio
import logging as log
from constants import *

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

### Constants ###

# Playback statuses
CLOSED = 0
OPENED = 1
CHANGING = 2
STOPPED = 3
PLAYING = 4
PAUSED = 5


### Globals ###

initialised = False
system_volume = None


### Functions ###

def init():
    """
    Initialises the media manager. Must be called before using any of the other functions in this module.
    """
    global system_volume
    global initialised

    log.info("Initialising media manager")

    # Init system volume access with pycaw
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    system_volume = cast(interface, POINTER(IAudioEndpointVolume))

    initialised = True


def get_volume() -> float:
    """
    Returns the system volume, expressed as a fraction between 0 (muted) and 1 (max volume)
    """
    log.log(TRACE, "Attempting to get system volume")
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    return system_volume.GetMasterVolumeLevelScalar() # type: ignore


def set_volume(volume: float):
    """
    Sets the system volume to the given value, specified as a fraction between 0 (muted) and 1 (max volume)
    """
    log.log(TRACE, "Attempting to set volume to %.2f", volume)
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    if volume < 0 or volume > 1: raise ValueError(f"Invalid volume level: {volume}")
    system_volume.SetMasterVolumeLevelScalar(volume, None) # type: ignore


def is_playing() -> bool:
    """
    Returns True if there is media currently playing, False otherwise
    """
    log.log(TRACE, "Attempting to retrieve current playback status")
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    return asyncio.run(_is_playing())


def toggle_playback() -> bool:
    """
    Attempts to toggle the playback of the current media
    """
    log.log(TRACE, "Attempting to toggle playback")
    # Not actually necessary but included for consistency
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    return asyncio.run(_toggle_playback())


def skip(forward = True) -> bool:
    """
    Attempts to skip to the next (default) or previous track and returns True if successful
    """
    log.log(TRACE, "Attempting to skip %s", "forawrd" if forward else "backward")
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    if forward: return asyncio.run(_skip_forward())
    else: return asyncio.run(_skip_backward())


def get_media_info() -> dict:
    """
    Returns a dictionary of information about the currently-playing media
    """
    log.log(TRACE, "Attempting to retrieve info for the current media")
    if not initialised: raise RuntimeError("Media manager accessed before initialisation!")
    return asyncio.run(_get_media_info())


### Internal Functions ###

async def _is_playing() -> bool:
    """
    [Internal] Attempts to retrieve the playback status of the current media, returning True if there is currently media
    playing and False otherwise
    """
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        pbinfo = current_session.get_playback_info() # No await because this isn't async
        return pbinfo.playback_status == PLAYING #type:ignore

    return False # Can't be any media playing if there's no session!


async def _toggle_playback() -> bool:
    """
    [Internal] Attempts to toggle the playback status of the current media and returns True if successful
    """
    sessions = await MediaManager.request_async()
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
    sessions = await MediaManager.request_async()
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
    sessions = await MediaManager.request_async()
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
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:

        info = await current_session.try_get_media_properties_async()
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
        info_dict['genres'] = list(info_dict['genres'])

        return info_dict

    return {}
    #raise Exception('No playback session currently running')