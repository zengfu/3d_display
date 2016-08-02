
import serial
import time
import struct
ypid=[10,1]

t=serial.Serial('com4',115200)
'''
t.write(ypid)
time.sleep(0.1)
n=t.inWaiting()
a=t.read(n)
print type(a[0])
print a[0]
def myadd(a,b):
    print a+b
print ord('a')
'''
f1=0.5
f2=3.75
print str(f2)
b=struct.pack('<2f',f1,f2)
t.write(b)
print len(b)






