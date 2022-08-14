"""
Device Serial Manager

Module that handles serial communication on the device end. Deals with setting up the connection and sending and receiving
messages.
"""

import sys
import utime
import uselect

import message_protocol

### Globals ###

MESSAGE_HANDLERS = {} # Dictionary mapping message types to handler functions

stdin_poll = uselect.poll()


### Functions ###

def register_handler(message_type: type, handler):
    """
    Registers the given handler function for the given message type.
    This will replace any existing handler for that message type.
    """
    MESSAGE_HANDLERS[message_type] = handler


def init():
    """
    Initialises the serial manager.
    """
    # Not sure why pylance doesn't like the following line
    stdin_poll.register(sys.stdin.buffer, uselect.POLLIN)  # type: ignore


def send(msg: message_protocol.Message):
    """
    Sends the given message to the host.
    """
    sys.stdout.buffer.write(msg.encode()) # type: ignore

    
def read(n: int):
    """
    Attempts to read and return n bytes from the serial input buffer. Returns None if no bytes are available.
    """
    # TODO: Check how this responds if the number of bytes available is not zero but is less than n
    #       In theory we shouldn't encounter this problem since we only read more than 1 byte when we know there is a
    #       message there (and how many bytes it should contain), but for robustness it would be good to nail this down
    return sys.stdin.buffer.read(n) if stdin_poll.poll(0) else None # type: ignore


def update():
    """
    Called from the device controller to update the serial manager.
    """
    while True: # Keep reading messages until there are none waiting

        id = read(1) # Try to read a byte from the input
        if not id: return # If there are no bytes waiting, we're done

        # Reconstruct message object
        msg = message_protocol.msg_from_id(id)
        if msg.size == 0: continue # Some messages contain no additional data - if so, move onto the next message

        # Decode additional message data
        data_bytes = read(msg.size)
        if not data_bytes: raise_msg_error(msg, 0)
        if len(data_bytes) < msg.size: raise_msg_error(msg, len(data_bytes))
        msg.decode(data_bytes)
        if type(msg) in MESSAGE_HANDLERS:
            MESSAGE_HANDLERS[type(msg)](msg) # Call the handler for this type of message to do whatever it needs to do


def raise_msg_error(msg, received):
    raise IndexError(f"Incomplete message: expected {msg.size} byte(s), received {received} byte(s). Message type: {type(msg)}")
