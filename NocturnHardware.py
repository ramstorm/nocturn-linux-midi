#!/usr/bin/python2

# Nocturn hardware functions module

#import core and util from usb for usb functions
import usb.core

#standard stuff
import sys
import binascii

class NocturnHardware( object ):
    
    vendorID = 0x1235
    productID = 0x000a
    initPackets=["b00000","28002b4a2c002e35","2a022c722e30","7f00"]

    ep = None
    ep2 = None
        

    def __init__( self ):
        dev = usb.core.find(idVendor=self.vendorID, idProduct=self.productID)
            
        if dev is None:
            raise ValueError('Device not found')
            sys.exit()

        cfg = dev[1]
        intf = cfg[(0,0)]

        self.ep = intf[1]
        self.ep2 = intf[0]
        
        try:
            dev.set_configuration()
            print "USB acquired: ", dev
        except usb.core.USBError as e:
            sys.exit('Something is wrong with your USB setup: \n' + str(e))

        # init routine - packet meaning unknown, reverse-engineered
        for packet in self.initPackets:
            self.ep.write(binascii.unhexlify(packet))

    def write( self, packet ):
        self.ep.write(packet)
    
    def read( self ):
        try:
            data = self.ep2.read(self.ep2.wMaxPacketSize,10)
            return data
        except usb.core.USBError:
            return
    
    def processedRead( self ):
        data = self.read()
        if data:
            print data[1:3]
        return data[1:3] if data else None

    # Sets the LED ring mode for a specific LED ring
    # possible modes: 0 = Start from MIN value, 1 = Start from MAX value, 2 = Start from MID value, single direction, 3 = Start from MID value, both directions, 4 = Single Value, 5 = Single Value inverted
    # The center LED ring can't be set to a mode (or I haven't found out how)
    def setLEDRingMode (self, ring, mode):
        if ((ring > 7) | (ring < 0)):
            raise NameError("The LED ring needs to be between 0 and 7")
        
        if ((mode < 0) | (mode > 5)):
            raise NameError("The mode needs to be between 0 and 5")

        self.write(chr(ring+0x48) + chr(mode << 4))

    # Sets the LED ring value
    # ring = 0-8
    # value = 0-127
    def setLEDRingValue (self, ring, value):
        if ((ring > 8) | (ring < 0)):
            raise NameError("The LED ring needs to be between 0 and 8")
        
        if ((value < 0) | (value > 127)):
            raise NameError("The LED ring value needs to be between 0 and 127")
        
        self.write(chr(0x40+ring) + chr(value))
        
    # Turns a button LED on or off
    # button = 0-16
    # val = 0 or 1
    def setButton (self, but, val):
        
        if ((but < 0) | (but > 15)):
            raise NameError("Button value needs to be between 0 and 15 (0x00 and 0x0F)")
        
        if ((val == 0) | (val == 1)):
            self.write(chr(0x70 + but) + chr(val))
            return

        raise NameError("Button value needs to be 0 or 1")
    
    def clearAll ( self ):
        for bb in range( 16 ):
            self.setButton( bb, 0 )
        for ll in range( 7 ):
            self.setLEDRingMode( ll, 0 )
            self.setLEDRingValue( ll, 0 )
