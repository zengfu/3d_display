
import serial
import time
import struct
ypid=[10,0,1]
t=serial.Serial('com4',115200)

t.write(ypid)
time.sleep(0.1)
n=t.inWaiting()
a=t.read(n)
print type(a[0])
print a[0]
print n





