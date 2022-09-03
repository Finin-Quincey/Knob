"""
Host Serial Manager

Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
messages.
"""

import serial

from constants import *
from serial_manager import SerialManager
import message_protocol as msp


class HostSerialManager(SerialManager):
    """
    Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
    messages.
    """

    def __init__(self):
        super().__init__()


    ### Context Manager Methods ###

    def __enter__(self):
        self.serial_connection = serial.Serial(COM_PORT, BAUD_RATE, timeout = 5)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.serial_connection.flush()
            self.serial_connection.close()
        except: # Plug was pulled so we can't do anything
            print("Device disconnected")


    ### Method Implementations ###

    def send(self, msg: msp.Message):
        self.serial_connection.write(msg.encode())

    def read(self, n: int):
        return self.serial_connection.read(n) if self.serial_connection.in_waiting else None