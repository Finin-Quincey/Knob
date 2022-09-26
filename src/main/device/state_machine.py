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

    def update(self):
        """
        Called each update cycle to perform state-specific logic.
        """
        pass


class IdleState(State):
    """
    Class representing the state of the device when idle, i.e. the knob is at rest and not pressed down.
    """
    # N.B. for simplicity, when it comes to implementing the VU meter this will NOT be done as a separate state because
    # that would result in extra complexity with the other states knowing which state to return to when they are done.
    # Instead, it should be implemented as a simple if statement and a bool to keep track of the playback status.
    # Edit: Then again, now we're creating state objects each time we could feasibly store a prev_state to go back to...

    def __init__(self):
        self.idle_start_time = utime.ticks_ms()
        self.initial_encoder_count = device.encoder.count # Used to detect when the knob has been rotated
        device.leds.set_colour((0, 0, 0)) # Turn off pixels to begin with
        #device.leds.set_colour((90, 255, 255)) # Green

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
        device.leds.display_fraction(self.volume, VOLUME_DISPLAY_COLOUR)

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
        
        device.leds.display_fraction(self.volume, VOLUME_DISPLAY_COLOUR) # Update displayed volume
        self.prev_count = device.encoder.count


class PressedState(State):
    """
    Class representing the state of the device while the button is pressed down, an intermediate state for several controls.
    """

    def __init__(self):
        self.hold_start_time = utime.ticks_ms()
        self.initial_encoder_count = device.encoder.count
        #device.leds.set_colour((240, 255, 255)) # Blue

    def update(self):

        like_time_exceeded = utime.ticks_ms() - self.hold_start_time > LIKE_HOLD_TIME
        
        if not device.encoder.is_switch_pressed(): # Button released
        
            if not like_time_exceeded:
                device.leds.set_colour((0, 0, 255))
                device.leds.crossfade(LED_TRANSITION_DURATION)
                device.serial_manager.send(msp.TogglePlaybackMessage()) # Short press: send play/pause message

            set_state(IdleState()) # Return to idle as soon as the button is released, regardless of hold duration
            return
        
        # Long press: send like/unlike message
        # This happens immediately after the like hold time, not when the button is ultimately released, because otherwise
        # the user would get no feedback as to when they have held it for long enough until after they release the button
        if like_time_exceeded:
            pass
            #dsm.send(LikeMessage()) # TODO
        
        if abs(encoder_delta(self.initial_encoder_count, device.encoder.count)) > ENCODER_DEADZONE:
            set_state(SkippingState(self.initial_encoder_count))
            return # Good practice even when it's the end of the method


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
            
            device.leds.crossfade(LED_TRANSITION_DURATION)
            set_state(IdleState())
            return


### Globals ###

_current_state = IdleState()

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
    _current_state = new_state


def is_in_state(state: type[State]):
    """
    Returns True if the current state is of the given type.
    """
    return isinstance(_current_state, state)


def update():
    """
    Called from the main program loop to update the state machine and perform state-specific logic.
    """
    _current_state.update()