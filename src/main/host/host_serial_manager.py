"""
Host Serial Manager

Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
messages.
"""

import serial
import serial.tools.list_ports as list_ports
from serial.serialutil import SerialException
import logging as log

from constants import *
from serial_manager import SerialManager
import message_protocol as msp

MESSAGE_LOG_BLACKLIST = [
    msp.VUMessage,
    msp.SpectrumMessage
]

class HostSerialManager(SerialManager):
    """
    Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
    messages.
    """

    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.connected_port = None

    # Override to add logging
    def register_handler(self, message_type: type, handler):
        super().register_handler(message_type, handler)
        log.debug("Registered new handler for %s", message_type)

    
    def handle(self, msg, b):
        log.debug("Received %s (raw bytes: %s)", msg, b)
        super().handle(msg, b)

    ### Context Manager Methods ###

    def __enter__(self):
        log.debug("Checking serial ports")
        if COM_PORT == "auto":
            for port in list_ports.comports():
                if port.vid == USB_VID and port.pid == USB_PID: # USB identifiers match, this should be a pico
                    log.debug("Found RP2040 device on port %s", port.name)
                    log.debug("Attempting to initialise serial connection on %s at %i baud", port.name, BAUD_RATE)
                    self.serial_connection = serial.Serial(port.name, BAUD_RATE, timeout = CONNECTION_TIMEOUT)
                    bytes = self.serial_connection.read(1) # Wait to receive ID or timeout
                    if len(bytes) > 0: # If we received something
                        log.debug("Received device ID: %d", int(bytes[0]))
                        if bytes[0] == DEVICE_ID: # Check ID matches
                            self.serial_connection.flush() # Clear out any bytes that are still in the input stream
                            self.connected_port = port # Record port info for future reference
                            return self # We are done here
                    else:
                        log.debug("Timed out waiting for device ID")
                    self.serial_connection.flush()
                    self.serial_connection.close()
                    # Otherwise try the next pico, if there is one
        else:
            log.debug("Attempting to initialise serial connection on %s at %i baud", COM_PORT, BAUD_RATE)
            self.serial_connection = serial.Serial(COM_PORT, BAUD_RATE, timeout = CONNECTION_TIMEOUT)
            return self
        raise SerialException("Unable to identify volume knob over USB")

    def __exit__(self, exc_type, exc_value, traceback):
        if self.serial_connection:
            try:
                self.serial_connection.flush()
                self.serial_connection.close()
                return
            except: # Plug was pulled so we can't do anything
                pass
        log.info("Device disconnected") # Only reachable if no serial connection


    ### Method Implementations ###

    def send(self, msg: msp.Message):
        if not self.serial_connection: return
        b = msg.encode()
        if type(msg) not in MESSAGE_LOG_BLACKLIST: log.debug("Sending %s (raw bytes: %s)", type(msg), b)
        self.serial_connection.write(b)

    def read(self, n: int):
        if not self.serial_connection: return None
        log.log(TRACE, "Attempting to read %i bytes", n)
        return self.serial_connection.read(n) if self.serial_connection.in_waiting else None