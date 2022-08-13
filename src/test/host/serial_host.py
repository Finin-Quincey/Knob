import serial
import time
import sys
sys.path.append("src/main/common")
import message_protocol as msp

BAUD_RATE = 115200
COM_PORT = "COM8"

# Timeout is in seconds
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout = 5)#, parity = serial.PARITY_EVEN, rtscts = 1)

#msg = msp.VolumeMessage(volume = 3)
#n = ser.write(msg.encode())

while(True):

    try:
        #msg = bytes([int(input("Enter number: "))])
        #msg = b'Ping\n'
        msg = bytes([1, 2, 3])# + b"\n"
        #msg = [0b10001010, 0b00100001, 0b00101101]
        n = ser.write(msg)#str(msg, "utf-16"))
        print(f"Sent {n} bytes: {str(msg)}")
    except(EOFError):
        break

    time.sleep(0.1)

    # This essentially allows you to debug the serial comms!
    # (ampy run won't work for debugging serial since it requires full use of the serial port itself)
    while(True):
        b = ser.readline()
        print(b)
        if not b: break

#b = ser.read(4)

#print(f"Received {str(b)}")

ser.flush()

ser.close()