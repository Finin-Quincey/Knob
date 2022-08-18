"""
Serial Manager

Base class for both host and device serial managers. Deals with message handler infrastructure and other logic common to both
sides of the serial connection.
"""

import message_protocol as msp


def raise_msg_error(msg, received):
    """
    Helper function for raising incomplete message errors; prints out the relevant info in human-readable form.
    """
    raise IndexError(f"Incomplete message: expected {msg.size} byte(s), received {received} byte(s). Message type: {type(msg)}")


# Implementation note: this would normally be an abstract base class (ABC) but the abc module isn't available in micropython
# Therefore this is simply a regular class that is *treated like* an ABC - all 'abstract' methods just raise errors

class SerialManager():
    """
    Base class for both host and device serial managers. Deals with message handler infrastructure and other logic common to both
    sides of the serial connection.
    """

    def __init__(self):
        """
        Creates and initialises a new serial manager.
        """
        self.message_handlers = {} # Dictionary mapping message types to handler functions


    def register_handler(self, message_type: type, handler):
        """
        Registers the given handler function for the given message type.
        This will replace any existing handler for that message type.
        """
        self.message_handlers[message_type] = handler


    def update(self):
        """
        Called from the main program loop to update the serial manager.
        """
        while True: # Keep reading messages until there are none waiting

            id = self.read(1) # Try to read a byte from the input
            if not id: return # If there are no bytes waiting, we're done

            # Reconstruct message object
            msg = msp.msg_from_id(id)

            # Decode additional message data
            if msg.size > 0: # Some messages contain no additional data
                data_bytes = self.read(msg.size)
                if not data_bytes: raise_msg_error(msg, 0)
                if len(data_bytes) < msg.size: raise_msg_error(msg, len(data_bytes))
                msg.decode(data_bytes)

            # Call the handler (if it exists) for this type of message to do whatever it needs to do
            if type(msg) in self.message_handlers:
                self.message_handlers[type(msg)](msg)


    ### Abstract Methods ###

    def send(self, msg: msp.Message):
        """
        Sends the given message via the serial connection.
        Subclasses should implement this with the relevant code for their end of the connection.
        """
        raise NotImplementedError("Attempted to call send() for the base SerialManager class")

        
    def read(self, n: int):
        """
        Attempts to read and return n bytes from the serial input buffer. Returns None if no bytes are available.
        Subclasses should implement this with the relevant code for their end of the connection.
        Read implementations must not block if no bytes are available.
        """
        raise NotImplementedError("Attempted to call read() for the base SerialManager class")