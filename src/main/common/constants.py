"""
Constants

File containing various global constants used by the host software, device software or both.
"""

# Serial comms
BAUD_RATE = 115200              # Baud rate for the serial communication
COM_PORT = "COM8"               # TODO: Make this not hardcoded
RECONNECT_DELAY = 5             # Time between connection attempts, in seconds

# Logging
TRACE = 5

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
ENCODER_DEADZONE = 3            # Rotations of fewer than this many encoder counts will be ignored (80 = 1 rev.)

VOLUME_DISPLAY_COLOUR = (0, 0, 255)   # Colour of the pixels when displaying the current volume

# List of all the exceptions in MicroPython (I think - certainly the most common ones anyway)
EXCEPTIONS = [                  # Byte pattern (reading *anticlockwise*)
    AssertionError,             # 00000000
    AttributeError,             # 10000000
    ImportError,                # 01000000
    IndexError,                 # 11000000
    KeyboardInterrupt,          # 00100000
    KeyError,                   # 10100000
    MemoryError,                # 01100000
    NameError,                  # 11100000
    NotImplementedError,        # 00010000
    OSError,                    # 10010000
    StopIteration,              # 01010000
    SyntaxError,                # 11010000
    SystemExit,                 # 00110000
    TypeError,                  # 10110000
    ValueError,                 # 01110000
    ZeroDivisionError           # 11110000
]