"""
Host Serial Manager

Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
messages.
"""

import serial
import serial.tools.list_ports as list_ports
from serial.serialutil import SerialException
import logging as log
import os
import pickle
import time
import binascii

from constants import *
from serial_manager import SerialManager
import message_protocol as msp

MESSAGE_LOG_BLACKLIST = [
    msp.LogMessage,
    msp.VUMessage,
    msp.SpectrumMessage
]


class SerialCache():
    """
    Class representing cached information about the serial connection. Handles saving and loading the cache file.
    """

    def __init__(self, serial_number: str) -> None:
        self.serial_number = serial_number

    def save(self, filename):

        log.debug("Saving serial cache")

        with open(filename, "wb") as f: # type: ignore  # Pylance gets confused by the MicroPython libs :/
            try:
                pickle.dump(self, f)
                log.debug("Cache file saved successfully")
            except pickle.PicklingError:
                log.exception("Encountered an error while writing serial cache")

    @classmethod     
    def load(cls, filename):

        if not os.path.exists(filename): # type: ignore
            log.debug("Serial cache not found")
            return None

        log.debug("Loading serial cache")
        
        with open(filename, "rb") as f: # type: ignore
            try:
                cache = pickle.load(f)
                log.debug("Cache file loaded successfully")
                return cache
            except pickle.UnpicklingError:
                log.exception("Encountered an error while loading serial cache")
                return None


class HostSerialManager(SerialManager):
    """
    Class that handles serial communication on the host end. Deals with setting up the connection and sending and receiving
    messages.
    """

    def __init__(self):
        super().__init__()
        log.info("Initialising serial manager")
        self.serial_connection = None

    # Override to add logging
    def register_handler(self, message_type: type, handler):
        super().register_handler(message_type, handler)
        log.debug("Registered new handler for %s", message_type)

    
    def handle(self, msg: msp.Message, raw: bytes):
        if type(msg) not in MESSAGE_LOG_BLACKLIST:
            log.debug("Received %s (raw bytes: %s)", msg, self._format_bytes(raw))
        super().handle(msg, raw)

    
    def _format_bytes(self, raw: bytes) -> str:
        """
        [Internal] Formats the given raw bytes as a hex string.
        
        #### Parameters
        ##### Required
        - `raw`: The bytes to format
        
        #### Returns
        The resulting hex string.
        """
        return binascii.hexlify(raw, sep = " ").decode("utf-8")


    ### Serial Helper Methods ###

    def _connect(self, com_port, baud_rate = BAUD_RATE):
        """
        [Internal] Attempts to connect to the specified port.
        
        #### Parameters
        ##### Required
        - `com_port`: The name of the COM port to connect to, e.g. `"COM3"`.
        ##### Optional
        - `baud_rate`: The baud rate to use for the connection. Defaults to `115200`.

        ---
        Once this method returns, `self.serial_connection` will contain the active `Serial` object if successful,
        or `None` if unsuccessful.
        """
        # Accepting the port name as a string rather than a ListPortInfo so it can be called without listing ports
        log.debug("Attempting to initialise serial connection on %s at %i baud", com_port, baud_rate)
        try:
            self.serial_connection = serial.Serial(com_port, baud_rate, timeout = CONNECTION_TIMEOUT, write_timeout = CONNECTION_TIMEOUT)
        except SerialException:
            # There may be a case in which we're trying to connect to the wrong Pico and for some reason it won't
            # connect (e.g. it's already in use by some other program) - in this case, we don't want to abort
            # connecting entirely, we just want to move on and try a different port, so we need to catch the error
            log.exception("Encountered SerialException while trying to connect") # Traceback logged automatically
        
    
    def _device_search(self):
        """
        [Internal] Searches available serial ports for volume knob devices and attempts to connect.
        
        This method first attempts to identify the device using the cached serial number, which is much faster and
        works regardless of device state. If this fails, it falls back to listening for `DEVICE_ID` on each port
        that matches the VID and PID (this should match only RPi Picos running MicroPython). If this succeeds, the
        new serial number is cached for future use. This method is slower because for each port, it must wait for
        the device to send an ID message, or until connection timeout.

        This setup allows the device to be automatically identified on first connection without the software knowing
        the serial number in advance. Once identified, subsequent connections can be made much more quickly and
        reliably, including after the computer has woken from sleep or has otherwise lost connection without
        returning the device to the startup (broadcasting) state. It is also COM-port-agnostic, so changes to COM
        port assignments have no effect on program operation. In the event that the cache file is lost, the software
        simply falls back to the listening process.

        ---
        Once this method returns, `self.serial_connection` will contain the active `Serial` object if successful,
        or `None` if unsuccessful.
        """
        # Originally I had planned to also cache the COM port to make things faster
        # This would be a good strategy if list_ports.grep() offered a speed advantage over just retreiving all
        # ports - however, it actually just calls comports() behind the scenes anyway (albeit lazily) and
        # apparently it doesn't work so well on windows? Either way, comports() seems to only take about 10ms
        # so for the amount this method will be called, it really makes no difference at all. Therefore I've
        # opted to keep things simple and just cache the serial number - we can always cache more info in future

        log.debug("Searching serial ports for RP2040 devices...")
        
        # Retrieve info for all available COM ports and filter based on VID and PID
        ports = [p for p in list_ports.comports() if p.vid == USB_VID and p.pid == USB_PID]
        if not ports:
            log.debug("No RP2040 devices found")
            return
        
        # Attempt to identify volume knob based on cached serial number if present
        cache = SerialCache.load(CACHE_FILENAME) # Load cached info
        if cache and cache.serial_number:
            log.debug("Checking connected RP2040 devices for cached serial number (%s)", cache.serial_number)
            matching_ports = [p for p in ports if p.serial_number == cache.serial_number]
            if matching_ports:
                if len(matching_ports) > 1: log.warning("More than one matching device found, using first match")
                port = matching_ports[0]
                log.debug("Successfully identified volume knob device on %s (S/N: %s)", port.name, port.serial_number)
                self._connect(port.name, BAUD_RATE)
                if self.serial_connection:
                    return # Connection successful, we are done
            else:
                log.debug("No matching devices found")
                
        # If we were unable to identify the device directly, fall back to listening for ID
        log.debug("Unable to identify device by serial number; listening for device type IDs instead")
        for port in ports:
            self._connect(port.name)
            if not self.serial_connection: continue # Connection failed, try the next port
            # Wait to receive device ID message or timeout
            # Because the host read() implementation is blocking, calling this directly should wait
            # until a message is received (or until read timeout)
            try:
                msg, raw = self.read_next_msg()
                if isinstance(msg, msp.IDMessage):
                    log.debug("Received device type ID: %d", msg.id)
                    if msg.id == DEVICE_TYPE_ID: # Check ID matches
                        log.debug("Successfully identified volume knob device on %s (S/N: %s)", port.name, port.serial_number)
                        if port.serial_number:
                            SerialCache(port.serial_number).save(CACHE_FILENAME)
                        else:
                            log.warning("Device serial number unavailable; caching skipped")
                        return # Connection successful, we are done
                else:
                    log.warning("Received unexpected message while listening for device type ID: %s (raw bytes %s)",
                                type(msg), self._format_bytes(raw))
           
            except SerialException:
                log.debug("Timed out waiting for device ID")
            
            self.serial_connection.flush()
            self.serial_connection.close()
            # Otherwise try the next pico, if there is one


    ### Context Manager Methods ###

    def __enter__(self):

        # When attempting to connect to the device over USB serial, we first search the COM ports for the PID, VID and
        # cached serial number. If that fails or the cache cannot be loaded, we attempt to discover the device from
        # scratch by listening for the unique ID on ports that match VID and PID, updating the cache if successful.
        
        # Setting COM port manually will override the above process and attempt to connect to that COM port without
        # any additional checks (though a warning will be printed if the PID or VID don't match)

        # COM port auto-detection
        if COM_PORT == "auto":
            self._device_search()

        # COM port set manually
        else:
            ports = [p for p in list_ports.comports() if p.name == COM_PORT]
            if len(ports) > 1: log.warning("More than one COM port found with name %s", COM_PORT)
            if ports[0].vid != USB_VID or ports[0].pid != USB_PID:
                log.warning("Device on %s does not match VID and/or PID", COM_PORT)
            self._connect(COM_PORT)
            
        # If connection failed, raise an exception to avoid entering the context
        if not self.serial_connection: raise SerialException("Unable to connect to volume knob over USB")
        # Otherwise, clear out any bytes that are still in the input stream and proceed to context
        # Note that flush(), reset_input_buffer() and reset_output_buffer() all do different things
        # I had assumed that flush() clears both buffers - turns out it does neither! It simply waits until
        # the output buffer is empty. See https://stackoverflow.com/questions/61596242/pyserial-when-should-i-use-flush
        self.serial_connection.reset_input_buffer()
        return self
    

    def __exit__(self, exc_type, exc_value, traceback):
        
        if not self.serial_connection:
            log.error("Null serial object") # Should not happen!
            return
        
        try:
            self.serial_connection.flush()
            time.sleep(0.5) # Give any remaining messages time to send (flush often doesn't work properly)
        except SerialException: # Plug was pulled or device errored so we can't do anything
            log.warning("Unable to flush serial buffer")
        finally:
            self.serial_connection.close()


    ### Method Implementations ###

    def send(self, msg: msp.Message):
        if not self.serial_connection: return
        raw = msg.encode()
        if type(msg) not in MESSAGE_LOG_BLACKLIST:
            log.debug("Sending %s (raw bytes: %s)", type(msg), self._format_bytes(raw))
        self.serial_connection.write(raw)

    def read(self, n: int):
        if not self.serial_connection: return None
        log.log(TRACE, "Attempting to read %i bytes", n)
        return self.serial_connection.read(n)
    
    def bytes_waiting(self) -> bool:
        if not self.serial_connection: return False
        return self.serial_connection.in_waiting > 0