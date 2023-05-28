import pystray

from PIL import Image

image = Image.open("src/main/systray_icon.png")

menu = pystray.Menu(
    pystray.MenuItem(
        text = "Open Settings",
        action = lambda icon, item: print(f"{item} clicked")
    ),
    pystray.MenuItem(
        text = "View Logs",
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