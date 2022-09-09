"""
Host Serial Manager

Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
messages.
"""

import serial
import logging as log

from constants import *
from serial_manager import SerialManager
import message_protocol as msp

MESSAGE_LOG_BLACKLIST = [
    msp.VUMessage
]

class HostSerialManager(SerialManager):
    """
    Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
    messages.
    """

    def __init__(self):
        super().__init__()

    # Override to add logging
    def register_handler(self, message_type: type, handler):
        super().register_handler(message_type, handler)
        log.debug("Registered new handler for %s", message_type)

    
    def handle(self, msg, b):
        log.debug("Received %s (raw bytes: %s)", msg, b)
        super().handle(msg, b)

    ### Context Manager Methods ###

    def __enter__(self):
        log.debug("Attempting to initialise serial connection on %s at %i baud", COM_PORT, BAUD_RATE)
        self.serial_connection = serial.Serial(COM_PORT, BAUD_RATE, timeout = 5)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.serial_connection.flush()
            self.serial_connection.close()
        except: # Plug was pulled so we can't do anything
            log.info("Device disconnected")


    ### Method Implementations ###

    def send(self, msg: msp.Message):
        b = msg.encode()
        if type(msg) not in MESSAGE_LOG_BLACKLIST: log.debug("Sending %s (raw bytes: %s)", type(msg), b)
        self.serial_connection.write(b)

    def read(self, n: int):
        log.log(TRACE, "Attempting to read %i bytes", n)
        return self.serial_connection.read(n) if self.serial_connection.in_waiting else None