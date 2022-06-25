"""
Message Protocol

Module that defines the types of messages that can be sent between the device and host, what data they contain, and
how to convert that data to and from bytes (encoding and decoding).

This class is common, meaning it is part of both the host Python program and the device MicroPython program. As such, it only
uses language elements that are common to both Python and MicroPython. Because the actual method of sending and receiving
messages differs between the device (stdin/out) and host (pyserial), this is done outside of this module. By making this class
common, it guarantees that the device and host interpret messages the same way.
"""

from typing import Type

### Constants ###
BAUD_RATE = 115200
COM_PORT = "COM8" # TODO: Make this not hardcoded

### Globals ###
MESSAGE_REGISTRY = [] # List of message types, index is the message ID


### Classes ###

# It may seem a bit overkill to go full object-oriented for this. A potential alternative is to use a proxy pattern with
# network handler classes for both device and host that inherit from a common base class, with functions for each type
# of message. This achieves the same goal of providing a contract for eactly what data goes into each type of message.
# However, the issue there is that we don't necessarily know the type of an incoming message (sometimes it can be inferred
# from context but on the host end especially, it could be anything). This means we would have to have a single centralised
# decode() function anyway, and then a switch statement for each kind of message (potentially broken out into other functions).
# This would then have to return a tuple of values including the ID so that the caller can then determine the type of message
# ... which kind of defeats the point

class Message:

    def __init__(self):
        """
        Creates a new message. Subclasses should override this if they need to send additional data. This
        must be done using optional arguments only, so that the decoder can construct a 'blank' instance before
        populating it via from_bytes().
        """
        pass

    def encode(self):
        """
        Encodes this message as a sequence of bytes and returns the result.
        Subclasses should not override this method! Override get_bytes() instead.
        (It's done this way so that the empty array can be created centrally, and so we can ensure that the
        ID always comes first no matter where super() is called, even if it is never called)
        """
        data = self.to_bytes([])
        data.insert(0, MESSAGE_REGISTRY.index(type(self)))
        return bytes(data)

    def to_bytes(self, data: list) -> list:
        """
        Called from encode() to populate the message with bytes of data. Subclasses can override this and
        populate it with whatever data is required. If no additional data (other than the message ID) is
        needed, this method need not be overridden.
        """
        return data

    def from_bytes(self, data: list):
        """
        Called from decode() to read this message's values from the given list of bytes. Subclasses can
        override this and do the reverse of whatever data was populated in to_bytes(). The recommended way
        to do this is using data.pop(0) to avoid needing to use indices.
        """
        pass


class VolumeRequestMessage(Message):
    """
    Message sent to request the current volume from the host.
    
    Direction: Device -> Host
    
    Additional data: None
    """
    pass # No additional data required


class VolumeMessage(Message):
    """
    Message sent to update the current volume level.
    
    Direction: Both (H -> D upon request, D -> H when knob turned)
    
    Additional data:
    - volume (1 byte, where 0 is muted and 255 is max. volume)
    """

    def __init__(self, volume = 0):
        self.volume = volume

    def to_bytes(self, data: list) -> list:
        data.append(self.volume)
        return data

    def from_bytes(self, data: list):
        self.volume = data.pop(0)


class TogglePlaybackMessage(Message):
    """
    Message sent to toggle the current play/pause status.
    
    Direction: Device -> Host
    
    Additional data: None
    """
    pass # No additional data required


class PlaybackStatusMessage(Message):
    """
    Message sent to update the current play/pause status.
    
    Direction: Host -> Device
    
    Additional data:
    - playing (1 byte, where 0 is paused and 1 is playing)
    """

    def __init__(self, playing = False):
        self.playing = playing

    def to_bytes(self, data: list) -> list:
        data.append(int(self.playing))  # type: ignore  # What the heck is wrong with this, vscode?
        return data

    def from_bytes(self, data: list):
        self.playing = bool(data.pop(0))


class SkipMessage(Message):
    """
    Message sent to skip between tracks.
    
    Direction: Device -> Host
    
    Additional data:
    - forward (1 byte, where 0 is backwards and 1 is forwards)
    """

    def __init__(self, forward = False):
        self.forward = forward

    def to_bytes(self, data: list) -> list:
        data.append(int(self.forward))  # type: ignore
        return data

    def from_bytes(self, data: list):
        self.forward = bool(data.pop(0))


### Functions ###

def register(message_class: Type):
    """
    Registers the given class as a message type. The class must inherit from Message.
    """
    if not issubclass(message_class, Message): raise TypeError("Cannot register message type; must inherit from Message")
    MESSAGE_REGISTRY.append(message_class)


def decode(data_bytes: bytes) -> Message:
    """
    Decodes the given bytes and reconstructs and returns the original Message object for further processing.
    """
    data = list(data_bytes)
    msg = MESSAGE_REGISTRY[data.pop(0)]() # Empty brackets because we're calling the constructor here
    msg.from_bytes(data)
    return msg


# Message registry
register(VolumeRequestMessage)
register(VolumeMessage)
register(TogglePlaybackMessage)
register(PlaybackStatusMessage)
register(SkipMessage)