import machine
import utime

from neopixel import Neopixel

### Local Constants ###

MAX_PIOS = 8 # Total number of PIOs (state machines) onboard the Pico
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
        self._transition_start = 0
        self._transition_duration = 0
        self._current_brightness_norm = 1
        self._led_states = [(0, 0, 0)] * self.led_count
        self._led_snapshot = [(0, 0, 0)] * self.led_count


    def update(self):

        f = 1
        
        if self.is_transition_active():

            elapsed = utime.ticks_ms() - self._transition_start
            f = min(elapsed / self._transition_duration, 1)

            if f == 1:
                # Transition finished, reset variables
                self._transition_duration = 0

        for i, led in enumerate(self._led_states):
            # The following line mixes the current state with the snapshot state
            hsv = [int(a * f + b * (1 - f)) for a, b in zip(led, self._led_snapshot[i])] # type: ignore
            # Actually set the pixels
            self._pixels.set_pixel(self._to_pixel_index(i), self._apply_gamma(hsv), how_bright = self._get_current_brightness())

        self._refresh_pixels()


    def set_pixel(self, index: int, hsv):
        """
        Sets the pixel at the given index to the given colour, with gamma correction applied.
        An index of 0 corresponds to the pixel above the USB; indices increase moving clockwise.
        """
        self._led_states[index] = hsv


    def set_colour(self, hsv):
        """
        Sets all pixels to the given colour, with gamma correction applied.
        """
        self._led_states = [hsv] * self.led_count # How neat is that?


    def clear(self):
        self.set_colour((0, 0, 0))


    def display_fraction(self, fraction: float, hsv, smoothing = 1.0):
        """
        Lights up the given fraction of the ring (clockwise from the back), with optional smoothing.
        """
        # TODO: Implement smoothing
        self.clear()

        f = fraction * self.led_count
        on_pixels = int(f)
        remainder = f - on_pixels

        for i in range(on_pixels):
            self.set_pixel(i, hsv)

        # For a fraction of 1, all the pixels are already on so no need for this
        if on_pixels < self.led_count: self.set_pixel(on_pixels, (hsv[0], hsv[1], hsv[2] * remainder))


    def display_bytes(self, b: bytes):
        """
        Debug function that can display up to 3 bytes in binary around the led ring.
        First byte is red, second byte is green, third is blue. Bytes are big-endian when read clockwise.
        Zeros are displayed as dim colours rather than off to prevent ambiguity around where each byte starts and ends.
        """
        self._pixels.clear()
        if b:
            for n, val in enumerate(b):
                for i in range(8):
                    pixel_index = n * 8 + i
                    if pixel_index >= self.led_count: break # Run out of pixels!
                    c = [0, 0, 0]
                    c[n] = 255 if (val >> i) & 0b00000001 else 10 # Make the zeros dim rather than completely off
                    self._pixels.set_pixel(pixel_index, c, MAX_BRIGHTNESS) # Don't modulate brightness for debug stuff

        self._refresh_pixels()


    def crossfade(self, t: int):
        """
        Starts a crossfade transition. The LED ring will take a 'snapshot' of its state when this method is called and
        crossfade between that and whatever new state is set over t milliseconds. Users may continue to set the colour
        during this time without affecting the transition.
        """
        if self.is_transition_active(): return # Ignore multiple requests
        self._transition_start = utime.ticks_ms()
        self._transition_duration = t
        self._led_snapshot = self._led_states.copy() # Shallow copy should be okay since we never modify hsv components in here


    def is_transition_active(self) -> bool:
        """
        Returns True if the LED ring currently has a transition (crossfade) active, False otherwise
        """
        return self._transition_duration > 0

    
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


    def _to_pixel_index(self, index: int) -> int:
        """
        Returns the actual pixel index corresponding to the given position around the device, where an input index of 0
        corresponds to the LED directly above the USB port and indices increase clockwise around the device.
        """
        if index > 23 or index < 0: raise ValueError(f"Invalid pixel index: {index}")
        return (self.offset - index) % self.led_count


    def _apply_gamma(self, hsv) -> tuple[int, int, int]:
        """
        Applies gamma correction to the given hsv colour and returns it as an rgb colour.
        """
        if len(hsv) != 3: raise ValueError("Unexpected colour format; must be a sequence of exactly 3 ints")
        # Apply gamma correction to the value channel before converting to RGB
        # This should give natural-looking results whilst being very cheap and simple to implement
        return self._pixels.colorHSV(int(hsv[0]/360 * 65535), hsv[1], GAMMA_LOOKUP[int(hsv[2])])

    
    def _get_current_brightness(self) -> float:
        """
        Returns the current brightness of the LED ring, taking transitions into account.
        """
        return self._current_brightness_norm * MAX_BRIGHTNESS