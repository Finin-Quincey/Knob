"""
State Machine

Handles state class definitions, transitions and logic.

Note that, unlike implementations in some other projects, the states here don't return the new state from their update methods.
This is simply because in this application, state changes don't usually happen from within state logic - most happen
'asynchronously' on receipt of messages.

Another difference is that a new state is created each transition, since there are variables that need resetting, and unlike C++,
Python has a garbage collector to deal with the old state objects for us :P
"""

import utime

from constants import *

import device_logger as log
import device_controller as device
import message_protocol as msp

class State:
    """
    Base class for device states.
    """

    def __init__(self):
        """
        Constructs a new instance of this state.
        """
        pass

    def should_display_audio(self) -> bool:
        """
        Called to determine whether the device should display audio visualisations in the current state.
        This need not return a constant; this behaviour may change within a single state.
        """
        return False # Default to not displaying audio visualisations

    def update(self):
        """
        Called each update cycle to perform state-specific logic.
        """
        pass


class StartupState(State):
    """
    Class representing the state of the device before connection has been established with the host program.
    """
    def __init__(self):
        device.leds.clear()
        self.last_broadcast_time = utime.ticks_ms()

    def update(self):

        # Send regular device ID messages
        if utime.ticks_ms() - self.last_broadcast_time > BROADCAST_INTERVAL:
            self.last_broadcast_time = utime.ticks_ms()
            device.serial_manager.send(msp.IDMessage(DEVICE_TYPE_ID))
        
        rotation = int(PIXEL_COUNT * utime.ticks_ms() / STARTUP_ANIMATION_PERIOD) % PIXEL_COUNT

        for i in range(PIXEL_COUNT):
            brightness = max(0, 1 - ((rotation - i) % PIXEL_COUNT) / STARTUP_ANIMATION_FADE_LENGTH)
            device.leds.set_pixel(i, hsv = (STARTUP_COLOUR[0], STARTUP_COLOUR[1], STARTUP_COLOUR[2] * brightness))


class IdleState(State):
    """
    Class representing the state of the device when idle, i.e. the knob is at rest and not pressed down.
    """
    # N.B. for simplicity, when it comes to implementing the VU meter this will NOT be done as a separate state because
    # that would result in extra complexity with the other states knowing which state to return to when they are done.
    # Instead, it should be implemented as a simple if statement and a bool to keep track of the playback status.
    # Edit: Then again, now we're creating state objects each time we could feasibly store a prev_state to go back to...

    def __init__(self):
        self.initial_encoder_count = device.encoder.count # Used to detect when the knob has been rotated
        device.leds.clear() # Turn off pixels to begin with
        #device.leds.set_colour((90, 255, 255)) # Green

    def should_display_audio(self):
        return True # Always display audio when idle

    def update(self):

        if device.encoder.is_switch_pressed():
            set_state(PressedState())
            return

        if abs(device.encoder.count - self.initial_encoder_count) > ENCODER_DEADZONE:
            device.serial_manager.send(msp.VolumeRequestMessage())
            return


class VolumeAdjustState(State):
    """
    Class representing the state of the device while the volume is being adjusted.
    """

    def __init__(self, initial_volume):
        self.volume = initial_volume
        self.idle_start_time = utime.ticks_ms()
        self.prev_count = device.encoder.count # Used to detect when the knob has been rotated
        device.leds.display_fraction(self.volume, VOL_DISPLAY_COLOUR)

    def update(self):

        if device.encoder.is_switch_pressed():
            set_state(PressedState())
            return

        if device.encoder.count == self.prev_count:
            elapsed = utime.ticks_ms() - self.idle_start_time
            if elapsed > VOL_DISPLAY_HOLD_TIME:
                device.leds.crossfade(LED_TRANSITION_DURATION)
                set_state(IdleState()) # Knob stationary for long enough, return to idle
                return
        else:
            # Calculate change in encoder count since the last update, wrapping to the -180 to 180 degree range
            delta = encoder_delta(self.prev_count, device.encoder.count)
            
            prev_vol = self.volume # Record previous volume level for comparison later
            self.volume += delta / (ENCODER_PPR * 4) # Update internal volume variable
            self.volume = min(max(self.volume, 0), 1) # Clamp to between 0 and 1
            if self.volume != prev_vol: # Optimisation: Don't send a message if the volume didn't change
                msg = msp.VolumeMessage(self.volume)
                device.serial_manager.send(msg)

            self.idle_start_time = utime.ticks_ms() # Knob moved, reset idle timer
        
        device.leds.display_fraction(self.volume, VOL_DISPLAY_COLOUR) # Update displayed volume
        self.prev_count = device.encoder.count


class PressedState(State):
    """
    Class representing the state of the device while the button is pressed down, an intermediate state for several controls.
    """

    def __init__(self):
        self.hold_start_time = utime.ticks_ms()
        self.initial_encoder_count = device.encoder.count
        self.like_msg_sent = False
        #device.leds.set_colour((240, 255, 255)) # Blue

    def should_display_audio(self):
        return True # Always display audio when pressed for now

    def update(self):

        like_time_exceeded = utime.ticks_ms() - self.hold_start_time > LIKE_HOLD_TIME
        
        if not device.encoder.is_switch_pressed(): # Button released
        
            if not like_time_exceeded:
                device.leds.set_colour(PLAY_PAUSE_COLOUR)
                device.leds.crossfade(LED_ANIMATION_DURATION)
                device.serial_manager.send(msp.TogglePlaybackMessage()) # Short press: send play/pause message

            set_state(IdleState()) # Return to idle as soon as the button is released, regardless of hold duration
            return
        
        # Long press: send like/unlike message
        # This happens immediately after the like hold time, not when the button is ultimately released, because otherwise
        # the user would get no feedback as to when they have held it for long enough until after they release the button
        if like_time_exceeded and not self.like_msg_sent:
            device.serial_manager.send(msp.LikeMessage())
            self.like_msg_sent = True
        
        if abs(encoder_delta(self.initial_encoder_count, device.encoder.count)) > ENCODER_DEADZONE:
            set_state(SkippingState(self.initial_encoder_count))
            return # Good practice even when it's the end of the method
        

class UnlikeAnimationState(State):
    """
    Class representing the state of the device while the unlike animation is playing.
    """

    def __init__(self):
        self.start_time = utime.ticks_ms()

    def update(self):

        progress = (utime.ticks_ms() - self.start_time) / LED_ANIMATION_DURATION

        if progress > 1 and not device.encoder.is_switch_pressed(): # Button released
            set_state(IdleState())
            device.leds.crossfade(LED_TRANSITION_DURATION)
            return
        
        for i in range(PIXEL_COUNT):
            brightness = min(1, max(0, abs(i/PIXEL_COUNT - 0.5) * 2 + 0.2 - progress**0.5) * 3) # sqrt progress so it starts fast
            hsv = (UNLIKE_COLOUR[0], UNLIKE_COLOUR[1], UNLIKE_COLOUR[2] * brightness)
            device.leds.set_pixel(i, hsv)


class SkippingState(State):
    """
    Class representing the state of the device while a track is being skipped.
    """

    def __init__(self, initial_encoder_count):
        self.idle_time = 0
        self.initial_encoder_count = initial_encoder_count
        #device.leds.set_colour((300, 255, 255)) # Magenta

    def update(self):

        delta = encoder_delta(self.initial_encoder_count, device.encoder.count)

        device.leds.display_dir_indicator(delta / 20, 200, 180)

        if not device.encoder.is_switch_pressed(): # Button released
            
            if abs(delta) > ENCODER_DEADZONE:
                device.serial_manager.send(msp.SkipMessage(delta > 0))
                device.leds.display_dir_indicator(2.5 if delta > 0 else -2.5, 0, 0)
            
            device.leds.crossfade(LED_ANIMATION_DURATION)
            set_state(IdleState())
            return


### Globals ###

_current_state = StartupState()

def encoder_delta(old_count: int, new_count: int) -> int:
    """
    Calculates the change between the two given encoder count values, wrapping to the -180 to 180 degree range
    """
    delta = new_count - old_count
    if delta < -ENCODER_PPR*2: delta += ENCODER_PPR*4 # Wraparound clockwise
    if delta >  ENCODER_PPR*2: delta -= ENCODER_PPR*4 # Wraparound anticlockwise
    return delta


def set_state(new_state):
    """
    Switches the device to the given state.
    """
    global _current_state
    if new_state == _current_state: return
    log.debug(f"Entering state: {type(new_state).__name__}")
    _current_state = new_state


def is_in_state(state: type[State]):
    """
    Returns True if the current state is of the given type.
    """
    return isinstance(_current_state, state)


def get_current_state() -> State:
    """
    Returns the current state object.
    """
    return _current_state


def update():
    """
    Called from the main program loop to update the state machine and perform state-specific logic.
    """
    _current_state.update()