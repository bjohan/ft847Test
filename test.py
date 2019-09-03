import serial
import sys
import python_cat_lib.cat
import python_cat_lib.ft847
sys.path.insert(0,'./CorboGPIB/trunk/src/')
import gpib
import rsSmfp
import numpy as np
import matplotlib.pyplot as plt
import time 
import sys
import scipy.io
import os
import re

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
smfp.modulation("AM_INT")
time.sleep(5)


print radio.receiverStatus()
print radio.transmitStatus()
print "Entering loop"

extAtt = 14.0
fc=436e6;

def measureAmplitudeSweep(radio, smfp, fc, levels):
    print levels
    radio.setFrequency(python_cat_lib.ft847.MAIN_VFO, fc)
    smfp.sigGenFrequency(fc/1e6)
    smfp.sigGenLevel(levels[0]+extAtt)
    snrs = []
    smets = []
    print "Sleeping for 5 seconds to let filters settle"
    time.sleep(5)
    for sigLevel in levels:
        smfp.sigGenLevel(sigLevel+extAtt)
        snr = smfp.receiverSnr()
        rxs = radio.receiverStatus()#, radio.transmitStatus()
        snrs.append(snr)
        smets.append(rxs['smeter'])
        print "level %f. \t snr %f. \t smeter %f"%(sigLevel, snr, rxs['smeter'])
    smfp.sigGenLevel(levels[0]+extAtt)
    return {'levels': levels, 'snr': snrs, 'smeter':smets}

def measureRadioFrequencySweep(radio, smfp, fc, level, offsets):
    snrs = []
    smets = []
    smfp.sigGenFrequency(fc/1e6)
    smfp.sigGenLevel(level+extAtt)
    print "Sleeping to let filters settle"
    time.sleep(5);
    for fo in offsets:
        smfp.disableDiode()
        radio.setFrequency(python_cat_lib.ft847.MAIN_VFO, fc+fo*1000)
        snr = smfp.receiverSnr()
        rxs = radio.receiverStatus()#, radio.transmitStatus()
        snrs.append(snr)
        smets.append(rxs['smeter'])
        print "offs %f [kHz]. \t snr %f. \t smeter %f"%(fo, snr, rxs['smeter'])
    return {'frequency offset': offsets, 'snr':snrs, 'smetser': smets}

def measureGeneratorFrequencySweep(radio, smfp, fc, level, offsets):
    snrs = []
    smets = []
    radio.setFrequency(python_cat_lib.ft847.MAIN_VFO, fc)
    smfp.sigGenLevel(level+extAtt)
    print "Sleeping to let filters settle"
    time.sleep(5)
    for fo in offsets:
        smfp.disableDiode()
        smfp.sigGenFrequency((fc+fo*1000)/1.0e6)
        snr = smfp.receiverSnr()
        rxs = radio.receiverStatus()#, radio.transmitStatus()
        snrs.append(snr)
        smets.append(rxs['smeter'])
        print "offs %f [kHz]. \t snr %f. \t smeter %f"%(fo, snr, rxs['smeter'])
    return {'frequency offset': offsets, 'snr':snrs, 'smetser': smets}

def measureSweep(radio, smfp, frequencies, level):
    snrs = []
    smets = []
    radio.setFrequency(python_cat_lib.ft847.MAIN_VFO, frequencies[0])
    smfp.sigGenLevel(level+extAtt)
    print "Sleeping to let filters settle"
    time.sleep(5)
    for f in frequencies:
        smfp.disableDiode()
        radio.setFrequency(python_cat_lib.ft847.MAIN_VFO, f)
        smfp.sigGenFrequency(f/1.0e6)
        time.sleep(1)
        snr = smfp.receiverSnr()
        rxs = radio.receiverStatus()#, radio.transmitStatus()
        snrs.append(snr)
        smets.append(rxs['smeter'])
        print "frequency %f  \t snr %f. \t smeter %f"%(f, snr, rxs['smeter'])
    return {'frequency': frequencies, 'snr':snrs, 'smetser': smets}

def slugify(value):
    import unicodedata
    value = value.decode('utf-8', 'ignore')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value

def plotResult(name, xkey, result):
    dk = []
    for key in result:
        if xkey != key:
            dk.append(key)

    #plt.figure()
    plt.hold(False)
    for key in dk:
        plt.plot(result[xkey], result[key])
        plt.hold(True)
    plt.xlabel(xkey)
    plt.title(name)
    plt.legend(dk)
    plt.grid(True)
    plt.pause(0.01)
    result['name'] = name
    result['xkey'] = xkey
    scipy.io.savemat(os.path.join(sys.argv[1], slugify(name)+'.mat'), result)

smfp.modInt(80)

def measureFrequency(name, radio, smfp, fc, levels, offsets):
    r = measureAmplitudeSweep(radio, smfp, fc, range(-140, -30, 5))
    plotResult(name+' amplitude sweep @'+str(fc), 'levels', r);
    r = measureRadioFrequencySweep(radio, smfp, fc, -65, np.arange(-12, 12, 1))
    plotResult(name+' filter vfo sweep@'+str(fc), 'frequency offset', r)
    r = measureGeneratorFrequencySweep(radio, smfp, fc, -65, np.arange(-12,12,1))
    plotResult(name+' generator frequency sweep @'+str(fc), 'frequency offset', r)


#am
def testFrequency(fc, radio, smfp, levels, offsets):
    smfp.modulation("AM_INT")
    radio.setMainVfoOperatingMode("AM(N)")
    measureFrequency("AM(N)",radio, smfp, fc, levels, offsets)

    smfp.modulation("AM_INT")
    radio.setMainVfoOperatingMode("AM")
    measureFrequency("AM",radio, smfp, fc, levels, offsets)

    smfp.modulation("FM_INT")
    radio.setMainVfoOperatingMode("FM(N)")
    measureFrequency("FM(N)",radio, smfp, fc, levels, offsets)

    smfp.modulation("FM_INT")
    radio.setMainVfoOperatingMode("FM")
    measureFrequency("FM",radio, smfp, fc, levels, offsets)

def sweepBand(radio, smfp, f, level):
    smfp.modulation("AM_INT")
    radio.setMainVfoOperatingMode("AM(N)")
    r = measureSweep(radio, smfp, f, level)
    plotResult("AM(N) signal sweep from %f to %f a %f dBm"%(f[0]/1e6, f[-1]/1e6, level), 'frequency', r)

    radio.setMainVfoOperatingMode("AM")
    r = measureSweep(radio, smfp, f, level)
    plotResult("AM signal sweep from %f to %f a %f dBm"%(f[0]/1e6, f[-1]/1e6, level), 'frequency', r)

    smfp.modulation("FM_INT")
    radio.setMainVfoOperatingMode("FM(N)")
    r = measureSweep(radio, smfp, f,level)
    plotResult("FM(N) signal sweep from %f to %f a %f dBm"%(f[0]/1e6, f[-1]/1e6, level), 'frequency', r)

    radio.setMainVfoOperatingMode("FM")
    r = measureSweep(radio, smfp, f,level)
    plotResult("FM signal sweep from %f to %f a %f dBm"%(f[0]/1e6, f[-1]/1e6, level), 'frequency', r)



def testBand(fl, fu, radio, smfp, levels, offsets):
    sweepBand(radio, smfp, np.arange(fl, fu, 100e3), -65)
    sweepBand(radio, smfp, np.arange(fl, fu, 100e3), -100)
    sweepBand(radio, smfp, np.arange(fl, fu, 100e3), -120)
    
    testFrequency(fl, radio, smfp, levels, offsets)
    testFrequency((fl+fu)/2, radio, smfp, levels, offsets)
    testFrequency(fu, radio, smfp, levels, offsets)

#testBand(432e6, 438e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
#testBand(144e6, 146e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
#testBand(50e6, 52e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
testBand(28e6, 30e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
testBand(24.9e6, 25e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
testBand(14e6, 14.350e6, radio, smfp, range(-140, 30, 5), np.arange(-12, 12,1))
plt.show()

