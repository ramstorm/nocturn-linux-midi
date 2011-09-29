# Control script for the Novation Nocturn - deals with hardware side
# of things. USB protocol reverse-engineered and implemented by felicitus,
# original code and cool game implementation at
# https://github.com/timoahummel/nocturn-game
#
## This program is free software. It comes without any warranty, to
## the extent permitted by applicable law. You can redistribute it
## and/or modify it under the terms of the Do What The Fuck You Want
## To Public License, Version 2, as published by Sam Hocevar. See
## http://sam.zoy.org/wtfpl/COPYING for more details.

import usb.core
import usb.util
import array
import sys
import time
import binascii

class Surface(object):
    pass

class Nocturn(Surface):
    """Provides a representation of the physical Novation Nocturn
    control surface"""

    vendorID = 0x1235
    productID = 0x000a
    initPackets=["b00000","28002b4a2c002e35","2a022c722e30","7f00"]
    
    ep = None
    ep2 = None

    encoders = range(64,71+1)
    toggleButtons = range(112,119+1)
    fnButtons = range(120,127+1)
    
    def __init__(self):
        super(Nocturn, self).__init__()
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
        except usb.core.USBError as e:
            sys.exit('Something is probably wrong with your USB setup - check udev rules, perhaps?')

        # init routine - packet meaning unknown, reverse-engineered
        for packet in self.initPackets:
            self.ep.write(binascii.unhexlify(packet))

        self.thingies = dict()
        for address in self.encoders:
            self.thingies[address] = RotaryEncoder(self,address,address-self.encoders[0])
        for address in self.toggleButtons:
            self.thingies[address] = ToggleButton(self,address, address-self.toggleButtons[0])
        #for address in self.fnButtons:
            #self.thingies[address] = FunctionButton(self,address)
        
    def write(self, packet):
        self.ep.write(packet)

    # Reads a packet and returns either "None" or the full packet.
    # The packet consists of at least 3 bytes, where the first
    # byte is irrelevant, the second byte is the control ID  (i.e. address)
    # and the third byte is the value
    def read(self):
        try:
            data = self.ep2.read(self.ep2.wMaxPacketSize,10)
            return data
        except usb.core.USBError:
            return None
    
    def poll(self):
        while True:
            p = self.read()
            if (p != None):
                self.callThingy(p[1],p[2])

    def callThingy(self, address, instruction):
        if (address in self.thingies):
            self.thingies[address].instruct(instruction)

class Thingy(object):
    def __init__(self, surface, address):
        self.address = address
        self.value = 0
        self.surface = surface

    def setValue(self, val):
        if (val < type(self).minValue): val = type(self).minValue
        if (val > type(self).maxValue): val = type(self).maxValue
        self.value = val

    def instruct(self, instruction):
        pass

class RotaryEncoder(Thingy):
    maxValue = 127
    minValue = 0
    sensitivity = 4
    def __init__(self, surface, address, number):
        super(RotaryEncoder, self).__init__(surface, address)
        self.ringModeAddress = chr(number+0x48)
        self.ringValAddress = chr(0x40+number)
    def setValue(self, val):
        super(RotaryEncoder, self).setValue(val)
        self.setRingValue(self.value)

    # Sets the LED ring mode
    # possible modes: 0 = Start from MIN value, 1 = Start from MAX value, 2 = Start from MID value, single direction, 3 = Start from MID value, both directions, 4 = Single Value, 5 = Single Value inverted
    # The center LED ring can't be set to a mode (or I haven't found out how)
    def setRingMode (self, mode):
        if ((mode < 0) | (mode > 5)):
            raise NameError("The mode needs to be between 0 and 5")
        self.surface.write(self.ringModeAddress + chr(mode << 4))
        self.setRingValue(self.value)

    # Sets the LED ring value
    # value = 0-127
    def setRingValue (self, value):        
        if ((value < 0) | (value > 127)):
            raise NameError("The LED ring value needs to be between 0 and 127")
        
        self.surface.write(self.ringValAddress + chr(value))

    def instruct(self, addValue):
        if (addValue > 127/2):
            addValue = 0 - (128-addValue)
        self.setValue(self.value + type(self).sensitivity * addValue)

class ToggleButton(Thingy):
    minValue = 0
    maxValue = 1
    pressValue = 127

    def __init__(self, surface, address, number):
        super(ToggleButton, self).__init__(surface,address)
        self.LEDAddress = chr(0x70 + number)
        self.value = 0
    # Turns button LED on or off
    # val = 0 or 1
    def setLED(self, val):
        if ((val == 0) | (val == 1)):
            self.surface.write(self.LEDAddress + chr(val))
            return

        raise NameError("Button value needs to be 0 or 1")

    def setValue(self, value):
        super(ToggleButton, self).setValue(value)
        self.setLED(value)

    def instruct(self, val):
        if (val == type(self).pressValue):
            self.setValue(type(self).maxValue-self.value)
    
