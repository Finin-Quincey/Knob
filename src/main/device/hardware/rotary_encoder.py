import micropython
from machine import Pin

micropython.alloc_emergency_exception_buf(100) # Recommended when using interrupts

class Encoder:
    """
    Class representing a quadrature rotary encoder with pushbutton.
    """
    
    def __init__(self, pin_a: int, pin_b: int, pin_sw: int, ppr: int):
        """
        Creates a new rotary encoder object and initialises the given pins accordingly.

        Parameters:
        - pin_a: The first pin attached to the encoder
        - pin_b: The second pin attached to the encoder
        - pin_sw: The pin attached to the encoder's built-in pushbutton
        - ppr: The number of pulses (cycles) per revolution
        """
        # Pin setup
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.pin_sw = Pin(pin_sw, Pin.IN, Pin.PULL_UP)

        # Interrupts
        self.pin_a.irq(self.handle_pulse, Pin.IRQ_RISING | Pin.IRQ_FALLING)
        self.pin_b.irq(self.handle_pulse, Pin.IRQ_RISING | Pin.IRQ_FALLING)

        # Init other variables
        self.cpr = ppr * 4
        self.count = 0
        self._last_pulse_pin = self.pin_a
        self._last_pulse_val = 0

    
    def handle_pulse(self, pin: Pin):
        """
        Interrupt handler for this encoder (internal); called each time the value of pin A or B changes.
        
        Parameters:
        - pin: The pin that changed
        """
        pin_val = pin.value() # Capture value of the tiggered pin as soon as possible in case it changes

        is_pin_b = pin is self.pin_b
        other_pin_val = self.pin_a.value() if is_pin_b else self.pin_b.value()

        if self._last_pulse_pin is pin and self._last_pulse_val == pin_val: return # Ignore if the same pin was pulsed twice

        self._last_pulse_pin = pin # Update last pulsed pin
        self._last_pulse_val = pin_val

        delta = 1 if is_pin_b == (pin_val == other_pin_val) else -1
        self.count = (self.count + delta) % self.cpr


    def is_switch_pressed(self):
        """
        Returns True if the switch is currently pressed down, False otherwise.
        """
        return self.pin_sw.value() == 0