import serial
import sys
import python_cat_lib.cat
import python_cat_lib.ft847
sys.path.insert(0,'./CorboGPIB/trunk/src/')
import gpib
import rsSmfp

print "Connecting to radio",
ioRadio = serial.Serial('/dev/ttyUSB0', baudrate= 57600, bytesize=8, parity = 'N', stopbits=2, timeout=1)
catif = python_cat_lib.cat.Cat(ioRadio)
radio = python_cat_lib.ft847.Ft847(catif);
print radio.receiverStatus()

print "Connecting to SMFP"
ioSmfp = serial.Serial('/dev/ttyUSB1', 115200, timeout=1)
gpibIf = gpib.GpibInterface(ioSmfp)
smfp = rsSmfp.RsSmfp(gpibIf,2)
smfp.reset()
smfp.receiverMode()
smfp.sigGenFrequency(436.0)
print radio.receiverStatus()
