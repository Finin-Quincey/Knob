import serial
import time

BAUD_RATE = 115200
COM_PORT = "COM8"

# Timeout is in seconds
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout = 5)#, parity = serial.PARITY_EVEN, rtscts = 1)

msg = b'Ping'
n = ser.write(msg)
print(f"Sent {n} bytes: {str(msg)}")

#time.sleep(5)

b = ser.read(4)

print(f"Received {str(b)}")

# while(True):
#     b = ser.read(4)
#     if b: print(b)
#     time.sleep(0.2)

ser.flush()

ser.close()