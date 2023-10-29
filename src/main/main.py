"""
main.py

Host code entry point. Responsible for the system tray icon/menu, as well as integrating with the rest of
the program.
"""

import pystray
from PIL import Image
from host.host_controller import HostController, ExitFlag


### Globals ###

img_connected = Image.open("src/main/systray_icon.png")
img_disconnected = Image.open("src/main/systray_icon_disconnected.png")

controller = HostController()


### Callbacks ###

def connect_callback():
    icon.icon = img_connected

def disconnect_callback():
    icon.icon = img_disconnected


### Setup Thread Loop ###

def run_host_process(icon):

    global controller

    #log.info("*** Starting volume knob host process ***")

    icon.visible = True

    while(True):

        controller.connect_callback = connect_callback
        controller.disconnect_callback = disconnect_callback
        
        exit_flag = controller.run()

        if exit_flag == ExitFlag.EXIT:
            #log.info("*** Exiting volume knob host process ***")
            icon.stop()
            return # Need to exit the loop here or it'll block icon.run() from exiting
        else:
            controller = HostController() # Recreate fresh controller object (old one should be gc-ed)
            #log.info("*** Restarting volume knob host process ***")


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

icon = pystray.Icon("volume_knob", icon = img_disconnected, title = "Knob", menu = menu, visible = True)

icon.run(setup = run_host_process)