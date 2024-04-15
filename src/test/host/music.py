import asyncio
import time

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

async def get_media_info():

    sessions = await MediaManager.request_async()

    # This source_app_user_model_id check and if statement is optional
    # Use it if you want to only get a certain player/program's media
    # (e.g. only chrome.exe's media not any other program's).

    # To get the ID, use a breakpoint() to run sessions.get_current_session()
    # while the media you want to get is playing.
    # Then set TARGET_ID to the string this call returns.

    current_session = sessions.get_current_session()
    if current_session:  # there needs to be a media session running
        #if current_session.source_app_user_model_id == TARGET_ID:
        info = await current_session.try_get_media_properties_async()

        # song_attr[0] != '_' ignores system attributes
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

        # converts winrt vector to list
        info_dict['genres'] = list(info_dict['genres'])

        return info_dict

    # It could be possible to select a program from a list of current
    # available ones. I just haven't implemented this here for my use case.
    # See references for more information.
    raise Exception('TARGET_PROGRAM is not the current media session')


async def toggle_playback() -> bool:

    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        success = await current_session.try_toggle_play_pause_async()
        return success

    raise Exception('No playback session currently running')


if __name__ == '__main__':
    
    # current_media_info = asyncio.run(get_media_info())
    # print(current_media_info)

    asyncio.run(toggle_playback())

    # devices = AudioUtilities.GetSpeakers()
    # interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    # volume = cast(interface, POINTER(IAudioEndpointVolume))
    # #print(volume.GetMasterVolumeLevelScalar())
    # #print(volume.GetVolumeStepInfo()) # Returns: "pnStep", "pnStepCount"
    # #print(volume.GetVolumeRange()) # Returns: "pfMin", "pfMax", "pfIncr"
    # volume.SetMasterVolumeLevelScalar(1, None)

    # while True:
    #     time.sleep(2)
    #     volume.SetMasterVolumeLevelScalar(0.5, None)
    #     time.sleep(2)
    #     volume.SetMasterVolumeLevelScalar(1, None)