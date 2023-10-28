"""
Spotify Hooks

Module responsible for interacting with the Spotify window.
"""

from constants import *
import logging as log
import pywinauto
import pywinauto.controls.hwndwrapper

### Constants ###
SPOTIFY_EXE_NAME = "Spotify.exe"
ESCAPE_KEY = "{ESC}"
LIKE_KEYBOARD_SHORTCUT = "%+b"


class SpotifyHooks():

    def __init__(self) -> None:
        self.app = None
        self.app32 = None
        self.window = None
        self.like_btn = None


    def init(self):
        """
        Initialises the Spotify hooks.
        """
        self.attempt_spotify_connection()
        self.locate_like_btn()


    def attempt_spotify_connection(self):
        """
        Attempts to find and connect to the Spotify GUI application.
        """
        pywinauto.warnings.simplefilter("ignore", category = UserWarning) # Shut up and do your job, pywinauto

        log.info("Attempting to connect to Spotify")

        # Get a list of running processes, as tuples of the form (pid, executable path, command line)
        for pid, exe_path, _ in pywinauto.application._process_get_modules_wmi():

            log.log(TRACE, "Checking process with ID %d", pid)
        
            # Filter out processes that don't belong to Spotify exe
            if not exe_path or SPOTIFY_EXE_NAME not in exe_path: continue

            log.log(TRACE, "Process ID %d belongs to Spotify executable", pid)
            
            # Use the lower-level API to dig out the necessary info
            # Need to set visible_only = False to find minimised windows - this doesn't affect background processes
            elements = pywinauto.findwindows.find_elements(backend = "uia", process = pid, visible_only = False)

            # elements should be empty for background processes, so this should filter out everything except the UI
            if not elements: continue

            log.debug("Found Spotify window (process ID %d)", pid)

            # Actually try to connect to the Spotify application
            self.app = pywinauto.application.Application(backend = "uia")
            self.app.connect(process = pid, top_level_only = False)

            self.app32 = pywinauto.application.Application(backend = "win32")
            self.app32.connect(process = pid, top_level_only = False)
            
            self.window = self.app32.top_window().wrapper_object()

            log.info("Spotify connection successful")
            break


    def check_spotify_connection(self) -> bool:
        """
        Checks that the spotify connection is still valid.
        """
        if not isinstance(self.window, pywinauto.controls.hwndwrapper.HwndWrapper): return False
        if self.app and self.window: return True # For some reason window is no longer a WindowWrapper, but a DialogWrapper... not sure why

        log.info("Unable to connect to Spotify")
        return False


    def locate_like_btn(self):

        if not self.check_spotify_connection(): return

        # Just to make pylance stop complaining, for some reason it won't recognise that we checked this above
        assert self.app
        assert self.window

        minimised = self.window.is_minimized()
        if minimised: self.window.restore()
        
        #controls_bar = app.Pane.Document.child_window(title_re = "^$", control_type = "Group")#, ctrl_index = 2)

        # pywinauto child window search is recursive, so the only reason to use multiple stages is to resolve ambiguity
        now_playing_group = self.app.Pane.Document.child_window(title_re = "Now playing.*", control_type = "Group")
        self.like_btn = now_playing_group.child_window(title_re = "(Save to|Remove from) Your Library", control_type = "Button")
        
        if minimised: self.window.minimize() # Re-minimise window if it was minimised before

        # Before this line, like_btn is just a *specification* for the button, i.e. an object describing the button - we haven't
        # actually tried to find it yet. This is actually done using the wrapper_object() method, which is normally called
        # implicitly (lazily) when access is actually needed. However, this operation is expensive (takes about 1s to complete),
        # so by calling it explicitly once we avoid having to wait 1s every time we need to query the button text
        try:
            self.like_btn = self.like_btn.wrapper_object() # <class 'pywinauto.controls.uia_controls.ButtonWrapper'>
        except (pywinauto.MatchError, pywinauto.ElementNotFoundError) as e:
            log.warn("Unable to locate like button in Spotify window; has the UI been updated?\n%s", e)
            return

        log.debug("Successfully located like button in Spotify window")


    def is_current_song_liked(self) -> bool:
        """
        Returns True if the current song is liked, False if not.
        """
        # Spotify somehow managed to break the toggle state function with one of their updates so now we have to read the button text
        # Matching part of the text and not case-sensitive to try and be as robust as possible to text changes
        return self.like_btn is not None and "remove" in self.like_btn.window_text().lower()
        #return like_btn is not None and like_btn.get_toggle_state()


    def toggle_liked_status(self):
        """
        Toggles the liked status of the current song.
        """
        if not self.check_spotify_connection(): return

        assert self.app
        assert self.window

        # Although we have access to the like button, like_btn.toggle() brings the window to the front so we need to use this instead
        # Also, it's slightly more robust in the case where we connected to spotify but were unable to find the like button
        minimised = self.window.is_minimized()
        # If we're currently typing in a text field (e.g. search), keystrokes are sent to the text field rather than the main app
        # Sending an esc key first restores focus to the main window, allowing it to receive the shortcut as normal
        # If we weren't in a text field, this does nothing
        self.window.send_keystrokes(ESCAPE_KEY)
        self.window.send_keystrokes(LIKE_KEYBOARD_SHORTCUT)
        if minimised: self.window.minimize() # Re-minimise the window if it was minimised previously