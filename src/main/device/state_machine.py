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

import device_controller as device
import device_serial_manager as dsm
import message_protocol as msp
from led_ring import VolumeEffect

class State:
    """
    Base class for device states.
    """

    def __init__(self):
        """
        Constructs a new instance of this state.
        """
        pass

    def on_entry(self):
        """
        Called immediately when the device transitions to this state, to perform any necessary initialisation.
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
    
    def on_entry(self):
        self.prev_count = device.encoder.count # Used to detect when the knob has been rotated
        #device.leds.set_colour((0, 0, 0))
        device.leds.set_colour((100, 255, 255)) # Green

    def update(self):

        if device.encoder.count != self.prev_count: # TODO: Figure out a nice way of storing prev count / changed info
            dsm.send(msp.VolumeRequestMessage())

        self.prev_count = device.encoder.count


class VolumeAdjustState(State):
    """
    Class representing the state of the device while the volume is being adjusted.
    """

    def __init__(self):
        self.idle_start_time = utime.ticks_ms()
        self.prev_count = device.encoder.count # Used to detect when the knob has been rotated
        device.leds.set_colour((180, 255, 255)) # Cyan

    def on_entry(self):
        device.leds.start_effect(VolumeEffect((0, 0, 255)))

    def update(self):

        if device.encoder.count == self.prev_count:
            if utime.ticks_ms() - self.idle_start_time > device.VOL_DISPLAY_HOLD_TIME:
                set_state(IdleState()) # Knob stationary for long enough, return to idle
                return
        else:
            self.idle_start_time = utime.ticks_ms() # Knob moved, reset idle timer

        self.prev_count = device.encoder.count


class PressedState(State):
    """
    Class representing the state of the device while the button is pressed down, an intermediate state for several controls.
    """

    def __init__(self):
        self.hold_start_time = utime.ticks_ms()
        self.initial_encoder_count = device.encoder.count
        device.leds.set_colour((240, 255, 255)) # Blue

    def on_entry(self):
        pass

    def update(self):

        like_time_exceeded = utime.ticks_ms() - self.hold_start_time > device.LIKE_HOLD_TIME
        
        if not device.encoder.is_switch_pressed(): # Button released
        
            if not like_time_exceeded:
                dsm.send(msp.TogglePlaybackMessage()) # Short press: send play/pause message

            set_state(IdleState()) # Return to idle as soon as the button is released, regardless of hold duration
            return
        
        # Long press: send like/unlike message
        # This happens immediately after the like hold time, not when the button is ultimately released, because otherwise
        # the user would get no feedback as to when they have held it for long enough until after they release the button
        if like_time_exceeded:
            pass
            #dsm.send(LikeMessage()) # TODO
        
        if abs(device.encoder.count - self.initial_encoder_count) > device.SKIP_COUNT_THRESHOLD:
            set_state(SkippingState(self.initial_encoder_count))
            return # Good practice even when it's the end of the method


class SkippingState(State):
    """
    Class representing the state of the device while a track is being skipped.
    """

    def __init__(self, initial_encoder_count):
        self.idle_time = 0
        self.initial_encoder_count = initial_encoder_count
        device.leds.set_colour((300, 255, 255)) # Magenta

    def on_entry(self):
        pass

    def update(self):

        if not device.encoder.is_switch_pressed(): # Button released
            
            if abs(device.encoder.count - self.initial_encoder_count) > device.SKIP_COUNT_THRESHOLD:
                dsm.send(msp.SkipMessage(device.encoder.count > 0))
            
            set_state(IdleState())
            return


### Globals ###

_current_state = IdleState()

def set_state(new_state):
    """
    Switches the device to the given state.
    """
    global _current_state
    if new_state == _current_state: return
    _current_state = new_state
    _current_state.on_entry()


def update():
    """
    Called from the main program loop to update the state machine and perform state-specific logic.
    """
    _current_state.update()