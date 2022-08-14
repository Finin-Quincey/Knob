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


def test_handler(msg: message_protocol.VolumeMessage):
    print(msg)


def init():
    """
    Initialises the serial manager.
    """
    # Not sure why pylance doesn't like the following line
    stdin_poll.register(sys.stdin.buffer, uselect.POLLIN)  # type: ignore
    #register_handler(message_protocol.VolumeMessage, lambda msg: sys.stdout.buffer.write(msg.volume))
    #register_handler(message_protocol.VolumeMessage, test_handler)


def send(msg: message_protocol.Message):
    """
    Sends the given message to the host.
    """
    sys.stdout.buffer.write(msg.encode()) # type: ignore

    
def read(n: int):
    return sys.stdin.buffer.read(n) if stdin_poll.poll(0) else None # type: ignore


def update(ring):
    """
    Called from the device controller to update the serial manager.
    """

    #while True:
    
    debug_led(ring, (45, 255, 255)) # Orange

    # waiting = stdin_poll.poll(0) # Poll stdin to check if any bytes have been received
    
    # debug_led(ring, (240, 255, 255)) # Blue
    
    # if not waiting: return # No bytes left to process so we're done here
    
    # debug_led(ring, (150, 255, 255)) # Green

    # # Reconstruct message object
    # id = sys.stdin.buffer.read(1) # Blocking, but we know there are bytes waiting so it'll return immediately

    id = sys.stdin.buffer.read(1) # Try to read a byte from the input

    debug_led(ring, (270, 255, 255)) # Purple

    utime.sleep(0.5)

    if not id: return # If there are no bytes waiting, we're done
    ring.display_bytes(id)
    
    utime.sleep(1)

    msg = message_protocol.msg_from_id(id)
    
    debug_led(ring, (150, 255, 255)) # Green

    utime.sleep(0.5)

    if not msg: return

    # Decode message
    if msg.size > 0:
        data_bytes = sys.stdin.buffer.read(msg.size)
        if not data_bytes: raise_msg_error(msg, 0)
        if len(data_bytes) < msg.size: raise_msg_error(msg, len(data_bytes))
        # ring.display_bytes(data_bytes)
        # sys.stdout.buffer.write(data_bytes)
        # utime.sleep(5)
        msg.decode(data_bytes)
        if type(msg) in MESSAGE_HANDLERS:
            MESSAGE_HANDLERS[type(msg)](msg) # Call the handler for this type of message to do whatever it needs to do


def raise_msg_error(msg, received):
    raise IndexError(f"Incomplete message: expected {msg.size} byte(s), received {received} byte(s). Message type: {type(msg)}")

def debug_led(ring, clr):
    ring.set_colour(clr)
    utime.sleep(1)
