"""
main.py

Host code entry point. Responsible for the system tray icon/menu, as well as integrating with the rest of
the program.
"""

import pystray
from PIL import Image
from host.host_controller import HostController, ExitFlag, Event


### Globals ###

img_connected = Image.open("src/main/systray_icon.png")
img_disconnected = Image.open("src/main/systray_icon_disconnected.png")

controller = HostController()


### Helper functions ###

def update_device_status(connected: bool):
    lines = icon.title.split("\n")
    device_status = "Connected" if connected else "Not connected"
    lines[0] = f"Knob - {device_status}"
    icon.title = "\n".join(lines)

def update_spotify_status(connected: bool):
    lines = icon.title.split("\n")
    spotify_status = "Connected to Spotify" if connected else "Spotify unavailable"
    lines[1] = f"{spotify_status}"
    icon.title = "\n".join(lines)


### Callbacks ###

def connect_callback():
    icon.icon = img_connected
    update_device_status(True)

def disconnect_callback():
    icon.icon = img_disconnected
    update_device_status(False)

def spotify_connect_callback():
    update_spotify_status(True)

def spotify_disconnect_callback():
    update_spotify_status(False)

 
### Setup Thread Loop ###

def run_host_process(icon):

    global controller

    # Icon setup
    icon.visible = True
    update_device_status(False)
    update_spotify_status(False)

    while True:

        # Register host process callbacks
        controller.set_callback(Event.DEVICE_CONNECT,       connect_callback)
        controller.set_callback(Event.DEVICE_DISCONNECT,    disconnect_callback)
        controller.set_callback(Event.SPOTIFY_CONNECT,      spotify_connect_callback)
        controller.set_callback(Event.SPOTIFY_DISCONNECT,   spotify_disconnect_callback)
        
        # Start main program loop
        exit_flag = controller.run()

        # Check whether program exited with restart code
        if exit_flag == ExitFlag.RESTART:
            controller = HostController() # Recreate fresh controller object (old one should be gc-ed)
            continue
        
        # Otherwise, clean up and exit the program
        icon.stop()
        return # Need to exit the loop here or it'll block icon.run() from exiting


### System Tray Menu Setup ###

menu = pystray.Menu(
    pystray.MenuItem(
        text = "Enable Lighting",
        action = lambda icon, item: print(f"{item} clicked"),
        checked = lambda item: True,
        default = True
    ),
    pystray.MenuItem(
        text = "Lock to Current App",
        action = lambda icon, item: print(f"{item} clicked"),
        #checked = lambda item: True,
        default = False
    ),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem(
        text = "Open Settings File",
        action = lambda icon, item: icon.notify(f"{item} clicked")
    ),
    pystray.MenuItem(
        text = "View Logs",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem(
        text = "Development Mode",
        action = lambda icon, item: controller.dev_mode()
    ),
    pystray.MenuItem(
        text = "Restart",
        action = lambda icon, item: controller.restart()
    ),
    pystray.MenuItem(
        text = "Quit",
        action = lambda icon, item: controller.exit()
    )
)

icon = pystray.Icon("volume_knob", icon = img_disconnected, title = "Knob\n", menu = menu, visible = True)

icon.run(setup = run_host_process)