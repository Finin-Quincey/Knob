import machine
import utime
from neopixel import Neopixel

### Local Constants ###

MAX_PIOS = 4 # Total number of PIOs (state machines) onboard the Pico
MAX_BRIGHTNESS = 15

# Lookup table for gamma-corrected 8-bit values
# https://learn.adafruit.com/led-tricks-gamma-correction/the-quick-fix
GAMMA_LOOKUP = [
      0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
      0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
      1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
      2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
      5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
     10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
     17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
     25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
     37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
     51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
     69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
     90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
    115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
    144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
    177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
    215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 
]


class LedRing:
    """
    Class representing a NeoPixel ring.
    
    This class is a wrapper around the neopixel library that adds support for gamma correction, along with
    various lighting effects. It also prevent issues with interrupts when sending data to the neopixels.
    """

    _next_pio = 0

    def __init__(self, pin: int, led_count: int, offset: int = 0, enable_gamma: bool = True):
        if LedRing._next_pio >= MAX_PIOS: raise IndexError("No more available state machines; cannot initialise LedRing")
        self._pixels = Neopixel(led_count, LedRing._next_pio, pin, "GRB")
        LedRing._next_pio += 1
        self.led_count = led_count
        self.offset = offset
        self.effect = None


    def update(self):
         
        if self.effect is None:
            return
        
        self.effect.update(self, utime.ticks_ms)


    def set_colour(self, hsv):
        self._pixels.fill(self._apply_gamma(hsv), how_bright = MAX_BRIGHTNESS)
        self._refresh_pixels()


    def display_bytes(self, b: bytes):
        """
        Debug function that can display up to 3 bytes in binary around the led ring.
        First byte is red, second byte is green, third is blue. Bytes are big-endian when read clockwise.
        Zeros are displayed as dim colours rather than off to prevent ambiguity around where each byte starts and ends.
        """
        for n, val in enumerate(b):
            for i in range(8):
                pixel_index = n * 8 + i
                if pixel_index >= self.led_count: break # Run out of pixels!
                c = [0, 0, 0]
                c[n] = 255 if (val >> i) & 0b00000001 else 10 # Make the zeros dim rather than completely off
                self._pixels.set_pixel(pixel_index, c, MAX_BRIGHTNESS)

        self._refresh_pixels()


    def set_effect(self, effect):
        self._pixels.clear()
        self.effect = effect
    
    ### Internal methods ###
    
    def _refresh_pixels(self):
        """
        Wrapper for Neopixel.show() that disables interrupts while it executes
        """
        # Sending data to the NeoPixels is timing critical, therefore it MUST NOT be interrupted or the LED drivers
        # will interpret the incomplete data, resulting in the wrong pixels turning on
        state = machine.disable_irq()
        self._pixels.show()
        machine.enable_irq(state)


    def _apply_gamma(self, hsv) -> tuple[int]:
        """
        Applies gamma correction to the given hsv colour and returns it as an rgb colour.
        """
        if len(hsv) != 3: raise ValueError("Unexpected colour format; must be a sequence of exactly 3 ints")
        # Apply gamma correction to the value channel before converting to RGB
        # This should give natural-looking results whilst being very cheap and simple to implement
        return self._pixels.colorHSV(int(hsv[0]/360 * 65535), hsv[1], GAMMA_LOOKUP[hsv[2]])


class Effect:
    """
    Base class for lighting effects.
    """

    def __init__(self):
        pass # Nothing here yet


    def update(self, led_ring, millis):
        pass # To be overridden by subclasses