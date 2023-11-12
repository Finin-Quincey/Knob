"""
Message Protocol

Module that defines the types of messages that can be sent between the device and host, what data they contain, and
how to convert that data to and from bytes (encoding and decoding).

This class is common, meaning it is part of both the host Python program and the device MicroPython program. As such, it only
uses language elements that are common to both Python and MicroPython. Because the actual method of sending and receiving
messages differs between the device (stdin/out) and host (pyserial), this is done outside of this module. By making this class
common, it guarantees that the device and host interpret messages the same way.
"""

from constants import *

### Globals ###
MESSAGE_REGISTRY = [] # List of message types, index is the message ID

### Classes ###

class Message:

    def __init__(self, size = 0):
        """
        Creates a new message. Subclasses should override this if they need to send additional data, calling this
        superconstructor to pass in the message size (in bytes, excluding the ID byte). This must be done using
        optional arguments only, so that the decoder can construct a 'blank' instance before populating it via from_bytes().
        """
        self.size = size

    def encode(self) -> bytes:
        """
        Encodes this message as a sequence of bytes and returns the result.
        Subclasses should not override this method! Override from_bytes() instead.
        (It's done this way so that the empty array can be created centrally, and so we can ensure that the
        ID always comes first no matter where super() is called, even if it is never called)
        """
        data = self.to_bytes([])
        data.insert(0, MESSAGE_REGISTRY.index(type(self)))
        return bytes(data)

    def decode(self, data_bytes: bytes):
        """
        Decodes this message from the given sequence of bytes.
        Subclasses should not override this method! Override to_bytes() instead.
        """
        # A bit overkill to have a separate wrapper method here but I want the conversion to list done inside the class
        # for consistency, plus we may want to do other stuff in this method later
        self.from_bytes(list(data_bytes))

    # Internal methods

    def to_bytes(self, data: list) -> list:
        """
        Called from encode() to populate the message with bytes of data. Subclasses can override this and
        populate it with whatever data is required. If no additional data (other than the message ID) is
        needed, this method need not be overridden. Ensure data is processed in the same order as from_bytes()
        (this includes calls to super())
        """
        return data

    def from_bytes(self, data: list):
        """
        Called from decode() to read this message's values from the given list of bytes. Subclasses can
        override this and do the reverse of whatever data was populated in to_bytes(). The recommended way
        to do this is using data.pop(0) to avoid needing to use indices. Ensure data is processed in the same
        order as from_bytes() (this includes calls to super())
        """
        pass


class LogMessage(Message):
    """
    Message sent to log a device-side event to the host side output stream(s).
    
    Direction: Device -> Host
    
    Additional data:
    - level (1 byte, representing the integer logging level as defined in the logging module)
    - msg (62 bytes, representing the UTF-8 encoded log message)

    ---
    Due to the fixed-length message system, this message must always contain the same number of bytes.
    The input string will be truncated or padded with spaces to make it exactly 62 bytes long. Trailing
    spaces should be removed on the receiving end before logging the message.
    """
    def __init__(self, level = 0, msg = ""):
        super().__init__(size = 63)
        self.level = level
        self.msg = msg

    def to_bytes(self, data: list) -> list:
        data.append(self.level)
        # Seems a bit silly to go from string to bytes to ints and then back to bytes but we've set things up
        # that way now! Maybe in future we'll change it so these functions handle raw bytes objects...
        chars = self.msg.encode("utf-8")
        for i in range(62):
            data.append(int(chars[i]) if i < len(chars) else SPACE_ASCII)
        return data

    def from_bytes(self, data: list):
        self.level = data.pop(0)
        self.msg = bytes(data).decode("utf-8").rstrip() # data should only contain the msg string now


class VolumeRequestMessage(Message):
    """
    Message sent to request the current volume from the host.
    
    Direction: Device -> Host
    
    Additional data: None
    """
    def __init__(self):
        super().__init__() # No additional data required


class VolumeMessage(Message):
    """
    Message sent to update the device with the current volume level.
    
    Direction: Both (H -> D upon request, D -> H when knob turned)
    
    Additional data:
    - volume (1 byte, where 0 is muted and 255 is max. volume)
    """

    def __init__(self, volume = 0.0):
        super().__init__(size = 1)
        if volume < 0 or volume > 1: raise ValueError(f"Invalid volume level: {volume}")
        self.volume = volume

    def to_bytes(self, data: list) -> list:
        data.append(int(self.volume * 255))
        return data

    def from_bytes(self, data: list):
        self.volume = data.pop(0) / 255 # Automatic conversion to float


class TogglePlaybackMessage(Message):
    """
    Message sent to toggle the current play/pause status.
    
    Direction: Device -> Host
    
    Additional data: None
    """
    def __init__(self):
        super().__init__() # No additional data required


class PlaybackStatusMessage(Message):
    """
    Message sent to update the device with the current play/pause status.
    
    Direction: Host -> Device
    
    Additional data:
    - playing (1 byte, where 0 is paused and 1 is playing)
    """

    def __init__(self, playing = False):
        super().__init__(size = 1)
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
        super().__init__(size = 1)
        self.forward = forward

    def to_bytes(self, data: list) -> list:
        data.append(int(self.forward))  # type: ignore
        return data

    def from_bytes(self, data: list):
        self.forward = bool(data.pop(0))


class VUMessage(Message):
    """
    Message sent to supply the device with stereo VU information.
    
    Direction: Host -> Device
    
    Additional data:
    - left (1 byte, representing the left channel volume)
    - right (1 byte, representing the right channel volume)
    """

    def __init__(self, left = 0.0, right = 0.0):
        super().__init__(size = 2)
        self.left  = left
        self.right = right

    def to_bytes(self, data: list) -> list:
        data.append(int(self.left  * 255))
        data.append(int(self.right * 255))
        return data

    def from_bytes(self, data: list):
        self.left  = data.pop(0) / 255 # Automatic conversion to float
        self.right = data.pop(0) / 255


class SpectrumMessage(Message):
    """
    Message sent to supply the device with stereo spectrum information.
    
    Direction: Host -> Device
    
    Additional data:
    - left (12 bytes, representing the left channel frequency spectrum)
    - right (12 bytes, representing the right channel frequency spectrum)
    """

    def __init__(self, left = None, right = None):
        super().__init__(size = SPECTRUM_FREQUENCY_BINS * 2)
        self.left =  [] if left  is None else left
        self.right = [] if right is None else right

    def to_bytes(self, data: list) -> list:
        for v in self.left:  data.append(int(v * 255))
        for v in self.right: data.append(int(v * 255))
        return data

    def from_bytes(self, data: list):
        self.data = data
        self.left  = [v/255 for v in data[:SPECTRUM_FREQUENCY_BINS]]
        self.right = [v/255 for v in data[SPECTRUM_FREQUENCY_BINS:]]


class LikeMessage(Message):
    """
    Message sent to like/unlike the current song.
    
    Direction: Device -> Host
    
    Additional data: None
    """
    def __init__(self):
        super().__init__() # No additional data required


class LikeStatusMessage(Message):
    """
    Message sent to update the device with the liked status of the current song.
    
    Direction: Host -> Device
    
    Additional data:
    - liked (1 byte, where 0 is not liked and 1 is liked)
    """

    def __init__(self, liked = False):
        super().__init__(size = 1)
        self.liked = liked

    def to_bytes(self, data: list) -> list:
        data.append(int(self.liked))  # type: ignore
        return data

    def from_bytes(self, data: list):
        self.liked = bool(data.pop(0))


class DisconnectMessage(Message):
    """
    Message sent on host program exit or restart to return the device to its startup state.
    
    Direction: Host -> Device
    
    Additional data: None
    """
    def __init__(self):
        super().__init__() # No additional data required


class ExitMessage(Message):
    """
    Message sent on activation of development mode to make the device exit to the REPL.
    
    Direction: Host -> Device
    
    Additional data: None
    """
    def __init__(self):
        super().__init__() # No additional data required


### Functions ###

def register(message_type: type[Message]):
    """
    Registers the given class as a message type. The class must inherit from Message.
    """
    #if not issubclass(message_class, Message): raise TypeError("Cannot register message type; must inherit from Message")
    MESSAGE_REGISTRY.append(message_type)
    

def msg_from_id(id_byte: bytes) -> Message:
    """
    Construct a blank message from its ID, ready to receive bytes of data.
    """
    id = int(id_byte[0])
    if id >= len(MESSAGE_REGISTRY): raise IndexError("Invalid message ID!")
    msg = MESSAGE_REGISTRY[id]() # Empty brackets because we're calling the constructor here
    return msg


# Message registry
register(LogMessage)
register(VolumeRequestMessage)
register(VolumeMessage)
register(TogglePlaybackMessage)
register(PlaybackStatusMessage)
register(SkipMessage)
register(VUMessage)
register(SpectrumMessage)
register(LikeMessage)
register(LikeStatusMessage)
register(DisconnectMessage)
register(ExitMessage)