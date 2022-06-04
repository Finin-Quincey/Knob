import pyautogui as ui
import time
import ctypes

# Constants
X_OFFSET = 334
Y_OFFSET = -43
LIKE_BUTTON_RGB = (30, 215, 96)
SEARCH_RADIUS = 50

prev_window = ui.getActiveWindow()

spotify_window = ui.getWindowsWithTitle("Spotify Premium")[0]

ui.PAUSE = 0.0001

print(prev_window.title)
print(spotify_window.title)

spotify_window.activate()

# Check the colour of the pixel in the centre of the like button
# This is not a reliable method but meh, if it works it works
corner = spotify_window.bottomleft
#print(ui.pixelMatchesColor(corner.x + X_OFFSET, corner.y - Y_OFFSET, LIKE_BUTTON_RGB))
y = corner.y + Y_OFFSET
result = ui.locateOnScreen("like_button.png", region = (0, y - SEARCH_RADIUS, 500, y + SEARCH_RADIUS))

# Inverted because this is before liking/un-liking the song (doesn't seem to work the other way)
print("Un-liked" if result else "Liked")

#ui.hotkey("alt", "shift", "b")

try:
    prev_window.minimize()
    prev_window.maximize()
except:
    pass