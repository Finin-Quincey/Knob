"""
main.py

Host code entry point. Responsible for the system tray icon/menu, as well as integrating with the rest of
the program.
"""

import pystray

from PIL import Image

image = Image.open("src/main/systray_icon.png")

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
        checked = lambda item: True
    ),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem(
        text = "Open Settings File",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.MenuItem(
        text = "View Logs",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem(
        text = "Development Mode",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.MenuItem(
        text = "Restart",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.MenuItem(
        text = "Quit",
        action = lambda icon, item: print(f"{item} clicked")
    )
)

icon = pystray.Icon("volume_knob", icon = image, title = "Knob", menu = menu, visible = True)

icon.run()

def run_host_process():
    from host import host_controller