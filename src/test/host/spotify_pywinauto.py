import pywinauto
import time

# app = pywinauto.application.Application(backend = "uia")
# app.connect(path = "Spotify.exe", top_level_only = False)

time.sleep(10) 

windows = pywinauto.findwindows.find_windows()

for h in windows:
    try:
        print(f"Processing {h}")
        w = pywinauto.application.Application(backend = "uia").connect(handle = h).top_window()
        print(w.window_text())
        if "Spotify Premium" in w.window_text():
            w.type_keys("{SPACE}")
            break
    except:
        pass
    
# window.type_keys("SPACE")