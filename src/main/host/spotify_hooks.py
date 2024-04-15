"""
Spotify Hooks

Module responsible for interacting with the Spotify window.
"""

from constants import *
import logging as log
import pywinauto
import pywinauto.controls.hwndwrapper
import time
import threading

### Constants ###
SPOTIFY_EXE_NAME = "Spotify.exe"
ESCAPE_KEY = "{ESC}"
LIKE_KEYBOARD_SHORTCUT = "%+b"
UPDATE_INTERVAL = 5


class SpotifyHooks():

    def __init__(self) -> None:
        self.app = None
        self.app32 = None
        self.window = None
        self.like_btn = None
        self.running = False
        self.current_liked_status = False
        self.toggle_request_flag = False


    def __enter__(self):
        """
        Initialises the Spotify hooks and starts the worker thread.
        """
        log.info("Starting Spotify hooks thread")
        self._thread = threading.Thread(target = self.run, name = "Spotify hooks thread")
        self.running = True
        self._thread.start()

    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Performs finalisation of Spotify hooks and shuts down the worker thread.
        """
        log.info("Stopping Spotify hooks thread")
        self.running = False # Tell run loop to stop at the end of this iteration (atomic)
        self._thread.join() # Wait for current loop iteration to end


    def run(self):
        """
        Spotify hooks thread run target. Handles the main update loop, periodically checking the connection.
        """
        last_update = time.time()
        while self.running:
            if time.time() - last_update > UPDATE_INTERVAL:
                if self._check_spotify_connection():
                    self._update_liked_status()
                else:
                    self._attempt_spotify_connection()
                    self._locate_like_btn()
                last_update = time.time()
            self._check_toggle_request()
            time.sleep(0.05)


    def _attempt_spotify_connection(self):
        """
        Attempts to find and connect to the Spotify GUI application.
        """
        pywinauto.warnings.simplefilter("ignore", category = UserWarning) # Shut up and do your job, pywinauto

        log.info("Attempting to connect to Spotify")
        
        t = time.perf_counter()

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

            log.log(TRACE, f"Spotify window identification took {time.perf_counter() - t:.3f}s")
            log.debug("Found Spotify window (process ID %d)", pid)

            # Actually try to connect to the Spotify application
            # Weirdly, we seem to need both backends - uia to get the button and win32 to send keystrokes
            # This feels like a bad idea but it seems to work just fine
            t = time.perf_counter()
            self.app = pywinauto.application.Application(backend = "uia")
            self.app.connect(process = pid, top_level_only = False)
            log.log(TRACE, f"uia connection took {time.perf_counter() - t:.3f}s")

            t = time.perf_counter()
            self.app32 = pywinauto.application.Application(backend = "win32")
            self.app32.connect(process = pid, top_level_only = False)
            log.log(TRACE, f"win32 connection took {time.perf_counter() - t:.3f}s")
            
            t = time.perf_counter()
            self.window_spec = self.app32.top_window() # Store so we can check if window exists later without waiting for a timeout
            self.window = self.window_spec.wrapper_object()
            log.log(TRACE, f"Window wrapper retrieval took {time.perf_counter() - t:.3f}s")

            log.info("Spotify connection successful")
            return
        
        log.info("Unable to connect to Spotify")


    def _check_spotify_connection(self) -> bool:
        """
        Checks that the Spotify connection is still valid.
        """
        return (self.app and self.app32         # If the app variables are None, we never connected in the first place
            and self.app32.is_process_running() # If this returns False, Spotify was running but has been closed (no need to check uia as well, both are the same process)
            and self.window_spec.exists()       # If this returns False, Spotify is minimised to the tray so we can't interact with it
        )


    def _locate_like_btn(self):

        if not self._check_spotify_connection(): return

        # Just to make pylance stop complaining, for some reason it won't recognise that we checked this above
        assert self.app
        assert self.window

        minimised = self.window.is_minimized()
        if minimised: self.window.restore()

        # pywinauto child window search is recursive, so the only reason to use multiple stages is to resolve ambiguity
        #now_playing_group = self.app.Pane.Document.child_window(control_type = "Group", depth = 2, title_re = "Now playing.*")
        #self.like_btn = now_playing_group.child_window(control_type = "Button", depth = 1, title_re = "(Save to|Remove from) Your Library")

        self.like_btn = self.app.Pane.Document.child_window(control_type = "Button", depth = 3, title_re = "Add to (Liked Songs|playlist)", found_index = 0)

        #self.status_bar = self.app.Pane.Document.child_window(control_type = "StatusBar", title_re = "(Added to|Removed from) Liked Songs\.StatusBar")

        #self.app.Pane.print_ctrl_ids(filename = "ctrl_ids.txt")
        
        # Attempt to improve speed by explicitly specifying each level, using ctrl_index is not robust but this is just for testing
        # This would be pretty difficult to implement in a robust way because the now playing group is stuck inside the toolbar,
        # which is a group with no title and no class name, making it impossible to identify dynamically... thanks Spotify
        # This did not speed things up anyway, which implies that the wrapper_object() function is just really slow regardless of
        # how much you narrow the search down.
        # toolbar_group = self.app.Pane.Document.child_window(control_type = "Group", ctrl_index = 2, depth = 1)
        # now_playing_group = toolbar_group.child_window(control_type = "Group", depth = 1, title_re = "Now playing.*")
        # self.like_btn = now_playing_group.child_window(control_type = "Button", depth = 1, title_re = "(Save to|Remove from) Your Library")

        if minimised: self.window.minimize() # Re-minimise window if it was minimised before

        # Before this line, like_btn is just a *specification* for the button, i.e. an object describing the button - we haven't
        # actually tried to find it yet. This is actually done using the wrapper_object() method, which is normally called
        # implicitly (lazily) when access is actually needed. However, this operation is expensive (takes about 2-3s to complete),
        # so by calling it explicitly once we avoid having to wait 1s every time we need to query the button text.
        try:
            t = time.perf_counter()
            self.like_btn = self.like_btn.wrapper_object() # <class 'pywinauto.controls.uia_controls.ButtonWrapper'>
            log.log(TRACE, f"Like btn wrapper retrieval took {time.perf_counter() - t:.3f}s")
        except (pywinauto.MatchError, pywinauto.ElementNotFoundError) as e:
            log.warning("Unable to locate like button in Spotify window; has the UI been updated?\n%s", e)
            return

        log.debug("Successfully located like button in Spotify window")


    def _update_liked_status(self):
        """
        [Internal] Called each update cycle to check the liked status of the current song.
        """
        # This may be a bit overkill but at least this way we always have a status available without needing two-way comms between threads.
        #print(self.status_bar.exists())

        # Spotify somehow managed to break the toggle state function with one of their updates so now we have to read the button text
        # Matching part of the text and not case-sensitive to try and be as robust as possible to text changes
        self.current_liked_status = self.like_btn is not None and "playlist" in self.like_btn.window_text().lower()
        #return like_btn is not None and like_btn.get_toggle_state() # Old version


    def _check_toggle_request(self):
        """
        [Internal] Checks if there is an outstanding like toggle request and if so, executes it.
        """
        if not self.toggle_request_flag: return

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

        self.toggle_request_flag = False

        log.debug("Toggled liked status of current song")


    ### External Methods ###

    def is_current_song_liked(self) -> bool:
        """
        Returns True if the current song is liked, False if not.
        """
        return self.current_liked_status


    def toggle_liked_status(self):
        """
        Toggles the liked status of the current song.
        """
        if self.toggle_request_flag: log.warn("Received a toggle request before the last one was executed!")
        self.toggle_request_flag = True
        log.debug("Like status toggle requested")