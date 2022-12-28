import pywinauto
import time
import win32gui, win32process

# See https://stackoverflow.com/questions/48723263/cannot-find-exe-with-pywinautos-find-windowtitle-program-exe
# def get_window_pid(title):
#     """
#     Finds the process ID associated with the given process name (.exe filename)
#     """
#     hwnd = win32gui.FindWindow(None, title)
#     threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
#     return pid

# pid = get_window_pid("Spotify.exe")

# w = pywinauto.application.Application(backend = "uia").connect(process = pid).top_window()

# print(w.window_text())

# SPOTIFY_PATH = r"C:\Users\qncyf\AppData\Roaming\Spotify\Spotify.exe"

# Right... lots to unpack here so bear with me

# Spotify is an awkward application to deal with, for two reasons:
# 1. It spawns multiple processes (6 usually), only one of which is the actual UI
# 2. The window title changes depending on the currently playing media
# This makes it a pain in the backside to identify! One approach would be to grab the media info
# from win32api and look for a window title with that in it, but this just *feels wrong* - what
# if Spotify updates and changes how the window title works?
# The much more reliable method is to use the .exe path, which *should* be simple since pywinauto
# allows us to connect to windows based on exe path. However, when there are multiple processes
# matching that exe file (as is the case with Spotify), it assumes we want the most recently launched
# one, where in fact the first Spotify process seems to always be the UI (although this should not be
# relied upon). Therefore, we have to:
# 1. Retrieve the list of processes ourselves using pywinauto's internal functions
# 2. Find the ones that belong to Spotify.exe
# 3. Take the process ID for each one and use more pywinauto internals to figure out which one is the UI
# 4. Once we have the pid for the actual UI, we can finally connect to that specific process and do stuff

for pid, exe_path, _ in pywinauto.application._process_get_modules_wmi():
    
    if not exe_path or "Spotify.exe" not in exe_path: continue
    
    # Use the lower-level API to dig out the necessary info
    elements = pywinauto.findwindows.find_elements(backend = "win32", process = pid)

    # elements should be empty for background processes, so this should filter out everything except the UI
    if not elements: continue

    print("Found Spotify UI")

    app = pywinauto.application.Application(backend = "uia")
    app.connect(process = pid, top_level_only = False, visible_only = False)

    print("Connected to Spotify application")

    # controls = app.windows(control_type = "Button")
    # for control in controls:
    #     print(control)

    w = app.window(visible_only = False).wrapper_object()
    print(w.window_text())

    print(w.get_show_state())

    controls_bar = app.Pane.Document.child_window(title = "", control_type = "Group", ctrl_index = 2)
    now_playing_group = controls_bar.child_window(title_re = "Now playing.*", control_type = "Group")
    like_btn = now_playing_group.child_window(control_type = "Button") # The like button is the only control of type Button

    # Before this line, like_btn is just a *specification* for the button, i.e. an object describing the button - we haven't
    # actually tried to find it yet. This is actually done using the wrapper_object() method, which is normally called
    # implicitly (lazily) when access is actually needed. However, this operation is expensive (takes about 1s to complete),
    # so by calling it explicitly once we avoid having to wait 1s every time we need to query the button text
    like_btn = like_btn.wrapper_object() # <class 'pywinauto.controls.uia_controls.ButtonWrapper'>

    print("Located like button")

    #w.send_keystrokes("%+b")

    while(True):
        time.sleep(1)
        print("Current song liked" if like_btn.get_toggle_state() else "Current song not liked")

#time.sleep(10) 

# Use the lower-level API to actually figure out what the criteria are
# The documentation helpfully doesn't provide examples :/
# kwargs = {}
# kwargs['backend'] = 'win32'
# elements = pywinauto.findwindows.find_elements(**kwargs)

# for e in elements:
#     print(e.name)
#     print(e.process_id)
#     if "Spotify" in e.rich_text:
#         w = pywinauto.application.Application(backend = "uia").connect(handle = e.handle).top_window()
#         break


# windows = pywinauto.findwindows.find_windows()

# for h in windows:
#     try:
#         print(f"Processing {h}")
#         w = pywinauto.application.Application(backend = "uia").connect(handle = h).top_window()
#         print(w.window_text())
#         print(w.backend.element_info_class())
#         # if "Spotify Premium" in w.window_text():
#         if "Spotify.exe" in w.app.process:
#             print("Found Spotify")
#             #w.type_keys("{SPACE}")
#             break
#     except:
#         pass
    
# window.type_keys("SPACE")