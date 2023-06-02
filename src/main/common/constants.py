"""
Constants

File containing various global constants used by the host software, device software or both.
"""

# Serial comms
BAUD_RATE = 115200                  # Baud rate for the serial communication
COM_PORT = "COM8"                   # TODO: Make this not hardcoded
RECONNECT_DELAY = 5                 # Time between connection attempts, in seconds

# Logging
TRACE = 5

# Pin number assignments for the Raspberry Pi Pico
ONBOARD_LED_PIN = 25                # Pin number used for the onboard LED on the Raspberry Pi Pico
PIXEL_DATA_PIN = 28                 # Pin number connected to the neopixel data in line
ENCODER_A_PIN = 22                  # Pin number connected to encoder output A
ENCODER_B_PIN = 21                  # Pin number connected to encoder output B
ENCODER_SW_PIN = 18                 # Pin number connected to the encoder switch output

# Encoder
ENCODER_PPR = 20                    # Encoder pulses per revolution (1 pulse = 4 counts)
ENCODER_DEADZONE = 3                # Rotations of fewer than this many encoder counts will be ignored (80 = 1 rev.)

# Neopixel ring
PIXEL_COUNT = 24                    # Number of LEDs in the neopixel ring
PIXEL_OFFSET = 20                   # Index of the first pixel clockwise from the back of the device (the one over the USB is last)

# Controls
VOL_DISPLAY_HOLD_TIME = 2000        # Time in ms after the knob stops turning that the volume will continue being displayed
LIKE_HOLD_TIME = 1500               # Time in ms that the button must be held for in order to like/unlike a song

# Colours
STARTUP_COLOUR = (0, 0, 220)        # Colour of the LED animation during startup
VOL_DISPLAY_COLOUR = (0, 0, 220)    # Colour of the pixels when displaying the current volume
PLAY_PAUSE_COLOUR = (0, 0, 220)     # Colour of the LED flash effect when toggling playback state
LIKE_COLOUR = (120, 219, 255)       # Colour of the LED flash effect when liking the current song
UNLIKE_COLOUR = (120, 219, 200)     # Colour of the LED effect when un-liking the current song

# Animations
LED_TRANSITION_DURATION = 350       # Duration of LED transition effects, in ms
LED_ANIMATION_DURATION = 600        # Duration of LED animation effects (like, play/pause, etc.), in ms
AUDIO_VISUALISER_BRIGHTNESS = 0.7   # Normalised brightness of the audio visualiser animation
STARTUP_ANIMATION_PERIOD = 1500     # Period of startup animation, in ms
STARTUP_ANIMATION_FADE_LENGTH = 12  # Number of pixels lit at once in the startup animation

# Spectrum analyser
AUDIO_SAMPLE_RATE = 48000           # Sampling rate for the audio from the loopback microphone
AUDIO_SAMPLES_PER_FRAME = 1024      # Number of audio samples (per channel) to record each frame (update cycle)
ROLLING_FRAMES = 4                  # Length of the rolling window over which the FFT is computed, expressed as a number of frames
SPECTRUM_FREQUENCY_BINS = 12        # Number of bins to quantise the frequency spectrum into (half the number of LEDs works best)
AUDIO_AVERAGING_WINDOW = 5          # Number of previous frames used to compute a moving average spectrum - controls 'smoothness'

# List of all the exceptions in MicroPython (I think - certainly the most common ones anyway)
EXCEPTIONS = [                      # Byte pattern (reading *anticlockwise*)
    AssertionError,                 # 00000000
    AttributeError,                 # 10000000
    ImportError,                    # 01000000
    IndexError,                     # 11000000
    KeyboardInterrupt,              # 00100000
    KeyError,                       # 10100000
    MemoryError,                    # 01100000
    NameError,                      # 11100000
    NotImplementedError,            # 00010000
    OSError,                        # 10010000
    StopIteration,                  # 01010000
    SyntaxError,                    # 11010000
    SystemExit,                     # 00110000
    TypeError,                      # 10110000
    ValueError,                     # 01110000
    ZeroDivisionError               # 11110000
]