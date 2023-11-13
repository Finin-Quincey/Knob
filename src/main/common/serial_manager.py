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
        while self.bytes_waiting(): # Keep reading messages until there are none waiting
            msg, b = self.read_next_msg()
            self.handle(msg, b)

        
    def read_next_msg(self):
        """
        Reads a single message from the input buffer and returns the resulting message object.
        
        #### Returns
        - `msg`: The resulting `Message` object.
        - `b`: A list of values representing the raw bytes that were read, for logging purposes.
        """
        id = self.read(1) # Read the first byte from the input - this should be the message ID
        b = [id]

        # Reconstruct message object
        msg = msp.msg_from_id(id)

        # Decode additional message data
        if msg.size > 0: # Some messages contain no additional data
            data_bytes = self.read(msg.size)
            if not data_bytes: raise_msg_error(msg, 0)
            if len(data_bytes) < msg.size: raise_msg_error(msg, len(data_bytes))
            msg.decode(data_bytes)
            b = list(data_bytes)
            b.insert(0, id)

        return msg, b

    
    def handle(self, msg, b):
        """
        Call the handler (if it exists) for this type of message to do whatever it needs to do
        Subclasses may extend functionality with e.g. logging
        """
        if type(msg) in self.message_handlers:
            self.message_handlers[type(msg)](msg)


    ### Abstract Methods ###

    def send(self, msg: msp.Message):
        """
        Sends the given message over the USB serial connection.
        
        #### Parameters
        ##### Required
        - `msg`: The `Message` object to send
        
        ---
        Subclasses should implement this with the relevant code for their end of the connection.
        """
        raise NotImplementedError("Attempted to call send() for the base SerialManager class")

        
    def read(self, n: int):
        """
        Reads and returns n bytes from the serial input buffer.
        
        #### Parameters
        ##### Required
        - `n`: The number of bytes to read

        #### Returns
        A `bytes` object containing the values read from the input buffer.
        
        ---
        This method is only called after checking that there are bytes waiting; as such the read
        operation may be blocking.

        Subclasses should implement this with the relevant code for their end of the connection.
        """
        raise NotImplementedError("Attempted to call read() for the base SerialManager class")
    

    def bytes_waiting(self) -> bool:
        """
        Checks whether there are bytes waiting in the serial input buffer.
        
        #### Returns
        `True` if there are bytes waiting, `False` if the buffer is empty.

        ---
        Subclasses should implement this with the relevant code for their end of the connection.
        """
        raise NotImplementedError("Attempted to call bytes_waiting() for the base SerialManager class")