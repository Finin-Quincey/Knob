from machine import Pin
import utime

led_pin = Pin(25, Pin.OUT)
p = Pin(0, Pin.OUT)

led_pin.value(1)

while True:
    led_pin.toggle()
    utime.sleep(1)