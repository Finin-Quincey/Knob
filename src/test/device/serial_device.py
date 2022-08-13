import sys
import utime
import uselect
from machine import Pin
import led_ring
import micropython

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

ONBOARD_LED_PIN = 25
PIXEL_DATA_PIN = 28
ENCODER_SW_PIN = 18

PIXEL_COUNT = 24
PIXEL_OFFSET = 20

sw_pin = Pin(ENCODER_SW_PIN, Pin.IN, Pin.PULL_UP)
led_pin = Pin(ONBOARD_LED_PIN, Pin.OUT)
led_pin.high() # Good check to see whether the script started successfully

# Get-out function: plug in while holding encoder button
if sw_pin.value() == 0:
    micropython.kbd_intr(3) # Enable interrupts
    for _ in range(5):
        utime.sleep_ms(200)
        led_pin.toggle()
    sys.exit() # Get-out

# Need this or the USB serial stream will interrupt when a 3 is sent
# Note that this effectively disables the REPL, making it impossible to interact with the pico!
# Therefore there should always be some kind of 'get-out' function 
micropython.kbd_intr(-1)

ring = led_ring.LedRing(PIXEL_DATA_PIN, PIXEL_COUNT, PIXEL_OFFSET)

ring.set_colour((180, 255, 255))

utime.sleep(5)

stdin_poll = uselect.poll()
# Not sure why pylance doesn't like the following line
stdin_poll.register(sys.stdin.buffer, uselect.POLLIN)  # type: ignore

def read():
    # Use stdin.buffer.read() rather than stdin.read() to read the data as bytes rather than a string
    return sys.stdin.buffer.read(1) if stdin_poll.poll(0) else None

try:
    while True:
        ring.set_colour((180, 255, 255))
        received = read() # sys.stdin.readline()
        ring.set_colour((90, 255, 255))
        # sys.stdout.write(str(type(ch))) # <class 'str'>
        # sys.stdout.write("\n")
        # Whatever we're getting out of read() is breaking display_bytes. I don't know what it is though
        # Need to convert val to int before we can do bitshift (Python lacks a primitive byte type)
        # b seems to come in as a str (which is a subclass of bytes) and when you iterate a string, it returns
        # strings of length 1
        # TODO: Define "little" (endian-ness) somewhere central and explicitly encode the data that way on the host end
        # TODO: Define encoding somewhere central
        ring.display_bytes(received)
        utime.sleep(1)
        ring.set_colour((240, 255, 255))
        utime.sleep(1)
    
 
except Exception as e:
    print(e) # TypeError: can't convert 'int' object to str implicitly
    ring.set_colour((50, 255, 255))
    utime.sleep(1)
    for i, ex_type in enumerate(EXCEPTIONS):
        if isinstance(e, ex_type):
            ring.display_bytes(bytes([i]))
            break