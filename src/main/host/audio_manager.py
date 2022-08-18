"""
Audio Manager

Contains functions for interacting with the system volume and playback controls.
"""

import asyncio

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

### Globals ###

initialised = False
system_volume = None


### Functions ###

def init():
    """
    Initialises the audio manager. Must be called before using any of the other functions in this module.
    """
    global system_volume
    global initialised

    # Init system volume access with pycaw
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    system_volume = cast(interface, POINTER(IAudioEndpointVolume))

    initialised = True


def get_volume() -> float:
    """
    Returns the system volume, expressed as a fraction between 0 (muted) and 1 (max volume)
    """
    if not initialised: raise RuntimeError("Audio manager accessed before initialisation!")
    return system_volume.GetMasterVolumeLevelScalar()


def set_volume(volume: float):
    """
    Sets the system volume to the given value, specified as a fraction between 0 (muted) and 1 (max volume)
    """
    if not initialised: raise RuntimeError("Audio manager accessed before initialisation!")
    if volume < 0 or volume > 1: raise ValueError(f"Invalid volume level: {volume}")
    system_volume.SetMasterVolumeLevelScalar(volume, None)


def toggle_playback() -> bool:
    """
    Attempts to toggle the playback of the current media
    """
    # Not actually necessary but included for consistency
    if not initialised: raise RuntimeError("Audio manager accessed before initialisation!")
    return asyncio.run(_toggle_playback())


def skip(forward = True) -> bool:
    """
    Attempts to skip to the next (default) or previous track and returns True if successful
    """
    if not initialised: raise RuntimeError("Audio manager accessed before initialisation!")
    if forward: return asyncio.run(_skip_forward())
    else: return asyncio.run(_skip_backward())


def get_media_info() -> dict:
    """
    Returns a dictionary of information about the currently-playing media
    """
    if not initialised: raise RuntimeError("Audio manager accessed before initialisation!")
    return asyncio.run(_get_media_info())


### Internal Functions ###

async def _toggle_playback() -> bool:
    """
    [Internal] Attempts to toggle the playback status of the current media and returns True if successful
    """
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_toggle_play_pause_async()
        # TODO: Make this get the playback status and return that instead
        return success

    raise Exception('No playback session currently running')


async def _skip_forward() -> bool:
    """
    [Internal] Attempts to skip to the next track and returns True if successful
    """
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_skip_next_async()
        return success

    raise Exception('No playback session currently running')


async def _skip_backward() -> bool:
    """
    [Internal] Attempts to skip to the previous track and returns True if successful
    """
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_skip_previous_async()
        return success

    raise Exception('No playback session currently running')


async def _get_media_info():
    """
    [Internal] Retrieves information about the currently-playing media and returns it as a dictionary
    """
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:

        info = await current_session.try_get_media_properties_async()
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
        info_dict['genres'] = list(info_dict['genres'])

        return info_dict

    raise RuntimeError('No playback session currently running')