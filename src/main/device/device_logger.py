"""
Device Logger

Helper functions for sending device-side log messages to the host program. This is a lightweight
device-side replacement for the logging module available in standard Python. Aside from sending the
messages over serial comms (and resulting char limit), the functions behave in much the same way.
"""

from constants import *
import message_protocol as msp
import device_controller as device

### Constants ###

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
# TRACE is already defined in constants module since it is shared by device and host

# Don't want these polluting the main constants file because they'll confuse the actual logging

def log(level, msg):
    """
    Logs the given message at the specified log level.
    
    #### Parameters
    ##### Required
    - `level`: The log level, as an integer between 0 and 255. Typically this will be one of the predefined constants.
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    device.serial_manager.send(msp.LogMessage(level, msg))


def critical(msg):
    """
    Logs the given message at the `CRITICAL` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(CRITICAL, msg)


def error(msg):
    """
    Logs the given message at the `ERROR` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(ERROR, msg)


def warning(msg):
    """
    Logs the given message at the `WARNING` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(WARNING, msg)


def info(msg):
    """
    Logs the given message at the `INFO` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(INFO, msg)


def debug(msg):
    """
    Logs the given message at the `DEBUG` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(DEBUG, msg)


def trace(msg):
    """
    Logs the given message at the `TRACE` level.
    
    #### Parameters
    ##### Required
    - `msg`: The message to send. Messages longer than 62 bytes (62 chars if all ASCII) will be truncated.
    """
    log(TRACE, msg)