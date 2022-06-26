"""
Device Serial Manager

Module that handles serial communication on the device end. Deals with setting up the connection and sending and receiving
messages.
"""

from machine import UART
import message_protocol

### Globals ###
uart = UART(0, message_protocol.BAUD_RATE) # TODO: Potentially move this to init

def init():
    """
    Initialises the serial manager.
    """
    pass # Nothing here yet


def update():
    """
    Called from the device controller to update the serial manager.
    """

    while True:

        waiting = uart.any() # Get number of bytes waiting in the buffer
        if not waiting: break # No bytes left to process so we're done here

        # Reconstruct message object
        id = uart.read(1) # Unlike sys.stdin.read(), uart.read() doesn't block
        assert id # Keeps pylance happy
        msg = message_protocol.msg_from_id(id)

        # Decode message
        if msg.size > 0:
            data_bytes = uart.read(msg.size)
            if not data_bytes: raise_msg_error(msg, 0)
            if len(data_bytes) < msg.size: raise_msg_error(msg, len(data_bytes))
            msg.decode(data_bytes)
            # Do something with the message


def raise_msg_error(msg, received):
    raise IOError(f"Incomplete message: expected {msg.size} byte(s), received {received} byte(s). Message type: {type(msg)}")