"""
Constants

File containing various global constants used by the host software, device software or both.
"""

# Serial comms
BAUD_RATE = 115200              # Baud rate for the serial communication
COM_PORT = "COM8"               # TODO: Make this not hardcoded

# Pin number assignments for the Raspberry Pi Pico
ONBOARD_LED_PIN = 25            # Pin number used for the onboard LED on the Raspberry Pi Pico
PIXEL_DATA_PIN = 28             # Pin number connected to the neopixel data in line
ENCODER_A_PIN = 22              # Pin number connected to encoder output A
ENCODER_B_PIN = 21              # Pin number connected to encoder output B
ENCODER_SW_PIN = 18             # Pin number connected to the encoder switch output

# Encoder
ENCODER_PPR = 20                # Encoder pulses per revolution (1 pulse = 4 counts)

# Neopixel ring
PIXEL_COUNT = 24                # Number of LEDs in the neopixel ring
PIXEL_OFFSET = 20               # Index of the first pixel clockwise from the back of the device (the one over the USB is last)

VOL_DISPLAY_HOLD_TIME = 2000    # Time in ms after the knob stops turning that the volume will continue being displayed
LIKE_HOLD_TIME = 2000           # Time in ms that the button must be held for in order to like/unlike a song
SKIP_COUNT_THRESHOLD = 5        # Number of encoder counts the knob must be rotated whilst pressed to skip a track (80 = 1 rev.)

# List of all the exceptions in MicroPython (I think - certainly the most common ones anyway)
EXCEPTIONS = [
    AssertionError,
    AttributeError,
    ImportError,
    IndexError,
    KeyboardInterrupt,
    KeyError,
    MemoryError,
    NameError,
    NotImplementedError,
    OSError,
    StopIteration,
    SyntaxError,
    SystemExit,
    TypeError,
    ValueError,
    ZeroDivisionError
]