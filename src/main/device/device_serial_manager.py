"""
Device Serial Manager

Class that handles serial communication on the device end. Deals with setting up the connection and sending and receiving
messages.
"""

import sys
import uselect

from constants import *
import message_protocol as msp
from serial_manager import SerialManager


class DeviceSerialManager(SerialManager):
    """
    Class that handles serial communication on the device end. Deals with setting up the connection and sending and receiving
    messages.
    """

    def __init__(self):
        super().__init__()
        self.stdin_poll = uselect.poll()
        # Not sure why pylance doesn't like the following line
        self.stdin_poll.register(sys.stdin.buffer, uselect.POLLIN) # type: ignore

    ### Method Implementations ###
    
    def send(self, msg: msp.Message):
        sys.stdout.buffer.write(msg.encode()) # type: ignore

    def read(self, n: int):
        # TODO: Check how this responds if the number of bytes available is not zero but is less than n
        #       In theory we shouldn't encounter this problem since we only read more than 1 byte when we know there is a
        #       message there (and how many bytes it should contain), but for robustness it would be good to nail this down
        return sys.stdin.buffer.read(n) # type: ignore
    
    def bytes_waiting(self) -> bool:
        return bool(self.stdin_poll.poll(0))