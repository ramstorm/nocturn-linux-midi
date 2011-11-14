# Control script for the Novation Nocturn - deals with hardware side
# of things. USB protocol reverse-engineered and implemented by felicitus,
# original code and cool game implementation at
# https://github.com/timoahummel/nocturn-game
#
# I have switched to Arch Linux, and at the moment, this script requires
# python2 from the repos and pyusb10 from AUR. It will also make
# extensive use of python-portmidi (also from AUR) once MIDI is
# implemented. YMMV on other distros.
#
## This program is free software. It comes without any warranty, to
## the extent permitted by applicable law. You can redistribute it
## and/or modify it under the terms of the Do What The Fuck You Want
## To Public License, Version 2, as published by Sam Hocevar. See
## http://sam.zoy.org/wtfpl/COPYING for more details.

#import core and util from usb for usb functions
import usb.core
import usb.util

#standard stuff
import array
import sys
import time
import binascii

#import pypm for midi functionality
import pypm


class Surface(object):
    """Reserved for future expansion of this script to other odd
    control surfaces."""
    pass

class Nocturn(Surface):
    """Provides a representation of the physical Novation Nocturn
    control surface"""

    vendorID = 0x1235
    productID = 0x000a
    initPackets=["b00000","28002b4a2c002e35","2a022c722e30","7f00"]
    

    MIDI_CHANNEL = 0
    
    MIDIDriver = None
    
    ep = None
    ep2 = None
    
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
            sys.exit('Something is wrong with your USB setup - check udev rules, perhaps?')

        # init routine - packet meaning unknown, reverse-engineered
        for packet in self.initPackets:
            self.ep.write(binascii.unhexlify(packet))
        
        # self.MIDIDriver = Midder(self.MIDI_IN_DEV,self.MIDI_OUT_DEV,self.LATENCY)
        
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
                pager.catchUSB(p[1],p[2])
            
    #~ def MIDIAdd(self,channel,controller,thingy):
        #~ if not (thingy in self.MIDIMap[channel][controller]):
            #~ self.MIDIMap[channel][controller].append(thingy)
    
    #~ def MIDIKill(self,channel,controller,thingy):
        #~ if not (channel == None or controller == None):
            #~ if thingy in self.MIDIMap[channel][controller]:
                #~ self.MIDIMap[channel][controller].remove(thingy)

    #~ def sendMIDI(self,channel,controller,value):
        #~ self.MIDIDriver.send(channel,controller,value)
        

class NocturnPager(object):
        
    def __init__(self, suface):
        self.pages = []
        self.pages.append(NocturnPage())
        self.currentPage = 0
        self.surface = surface
    
    def nextPage(self):
        self.currentPage += 1
        
    def prevPage(self):
        self.currentPage -= 1
        
    def addPage(self):
        self.pages.append(NocturnPage())
    
    def catchUSB (self, address, instruction):
        pages[currentPage].callThingy(address, instruction)

class NocturnPage(object):
    encoders = range(64,71+1)
    toggleButtons = range(112,119+1)
    fnButtons = range(120,127+1)
    
    def __init__(self):
        self.thingies = dict()
        self.surface = surface
        for i, address in enumerate(self.encoders):
            self.thingies[address] = RotaryEncoder(surface,address,address-self.encoders[0])
        for address in self.toggleButtons:
            self.thingies[address] = ToggleButton(surface,address,address-self.toggleButtons[0])
    
    def callThingy(self, address, instruction):
        if (address in self.thingies):
            self.thingies[address].instruct(instruction)
    

class Thingy(object):
    
    MIDIChannel = None
    MIDIController = None
    
    def __init__(self, surface, address):
        self.address = address
        self.value = 0
        self.surface = surface
    
    def __str__(self):
        return self.address
    
    def __eq__(self,other):
        return self.address == other.address

    def setValue(self, val):
        if (val < type(self).minValue): val = type(self).minValue
        if (val > type(self).maxValue): val = type(self).maxValue
        self.value = val
        self.surface.sendMIDI(self.MIDIChannel,self.MIDIController,self.value)

    def instruct(self, instruction):
        pass

class RotaryEncoder(Thingy):
    maxValue = 127
    minValue = 0
    sensitivity = 4
    ringModeOffset = 0x48
    ringValOffset = 0x40
    
    def __init__(self, surface, address, number):
        super(RotaryEncoder, self).__init__(surface, address)
        self.ringModeAddress = chr(self.ringModeOffset+number)
        self.ringValAddress = chr(self.ringValOffset+number)
    def setValue(self, val):
        super(RotaryEncoder, self).setValue(val)
        self.setRingValue(self.value)

    # Sets the LED ring mode
    # possible modes: 0 = Start from MIN value, 1 = Start from MAX value, 2 = Start from MID value, single direction,
    #                 3 = Start from MID value, both directions, 4 = Single Value, 5 = Single Value inverted
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
            
class Midder(object):
    CC_OFFSET = 0xb0
    
    def __init__(self, input, output, lat):
        self.dev = dev
        
        #Initialize pypm - I'm told bad things will happen otherwise
        pypm.Initialize()
        self.MidiOut = pypm.Output(output,lat)
        self.MidiIn = pypm.Input(input)
        
    def send(self,channel,cc, val):
        self.MidiOut.WriteShort(CC_OFFSET+channel,cc,val)
    def recv(self):
        pass


n = Nocturn()
n.poll()
