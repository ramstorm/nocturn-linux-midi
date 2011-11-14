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

#import configurator to supply configuration values
from configurator import *
    

class Nocturn(object):
    """Respresentation of physical device. Contains references to physical
    buttons, encoders on device, reference to USB communication, and reference
    to MIDI communication."""
    thingies = None
    
    def __init__(self):
        configurator = Configurator('default.conf')
        
        encoders = range(64,71+1)
        toggleButtons = range(112,119+1)
        fnButtons = range(120,127+1)
    
        self.thingies = dict()
        
        self.encoderList = []
        self.encoderList.append(RotaryEncoder(self,74,0))
        
        self.buttonList=[]
        
        for address in encoders:
            self.thingies[address] = RotaryEncoder(self,address,
                                                   1+address-encoders[0])
            self.encoderList.append(self.thingies[address])
            
        for address in toggleButtons:
            self.thingies[address] = ToggleButton(self,address,
                                                  1+address-toggleButtons[0])
            self.buttonList.append(self.thingies[address])
        
        self.usber = Usber(configurator.getUSBSettings())
        self.midder = Midder(configurator.getMIDISettings())
        self.pageContainer = PageContainer(self,configurator)
        
        self.syncPage()
        self.resetThingies()
    
    def syncPage(self):
        page = self.pageContainer.getCurrentPage()
        types = ['encoder','button']
        
        for type in types:
            for i, doodad in enumerate(self.getList(type)):
                doodad.connectControlUnit(page.getControlUnit(type,i))
    
    def getList(self,type):
        if type == 'encoder':
            return self.encoderList
        elif type == 'button':
            return self.buttonList
        
    def getEncoderList(self):
        return self.encoderList
    
    def getMidder(self):
        return self.midder
    
    def getUsber(self):
        return self.usber
    
    def run(self):
        try:
            while True:
                p = self.usber.read()
                if p != None:
                    self.callThingy(p[1], p[2])
                # need to poll midder here
        except KeyboardInterrupt:
            print "Keyboard interrupt received, ending run..."
            self.resetThingies()
            pass

   
    def callThingy(self, address, instruction):
        if (address in self.thingies):
            print "Calling thingy with address = {}".format(address)
            print self.thingies[address]
            self.thingies[address].instruct(instruction)
            
    def getCurrentPage(self):
        return self.pageContainer.getCurrentPage()
    
    def getThingy(self, type, number):
        if type == 'encoder':
            return self.encoderList[number]
        elif type == 'button':
            return self.buttonList[number]
    
    def resetThingies(self):
        for encoder in self.encoderList:
            encoder.setValue(0)
        for button in self.buttonList:
            button.setValue(0)
        
class Thingy(object):
    """Abstract class of physical control unit reference."""
    def __init__(self, surface, address):
        self.address = address
        self.value = 0
        self.surface = surface
    
    def __str__(self):
        return str("Thingy, address = {}".format(self.address))
    
    def __eq__(self,other):
        return self.address == other.address

    def setValue(self, val):
        if (val < type(self).minValue): val = type(self).minValue
        if (val > type(self).maxValue): val = type(self).maxValue
        self.value = val

    def connectControlUnit(self,cu):
        self.controlUnit = cu
    
    def instruct(self,instruction):
        self.controlUnit.act(self.value)
        
class RotaryEncoder(Thingy):
    """Concrete class referring to physical rotary encoder on the Nocturn."""
    maxValue = 127
    minValue = 0
    sensitivity = 4
    ringModeOffset = 0x48
    ringValOffset = 0x40
    
    def __init__(self, surface, address, number):
        super(RotaryEncoder, self).__init__(surface, address)
        self.ringModeAddress = chr(self.ringModeOffset+number-1)
        self.ringValAddress = chr(self.ringValOffset+number-1)
    
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
        self.surface.getUsber().write(self.ringModeAddress + chr(mode << 4))
        self.setRingValue(self.value)

    # Sets the LED ring value
    # value = 0-127
    def setRingValue (self, value):        
        if ((value < 0) | (value > 127)):
            raise NameError("The LED ring value needs to be between 0 and 127")
        
        self.surface.getUsber().write(self.ringValAddress + chr(value))

    def instruct(self, addValue):
        if (addValue > 127/2):
            addValue = 0 - (128-addValue)
        self.setValue(self.value + type(self).sensitivity * addValue)
        super(RotaryEncoder, self).instruct(self.value)

class ToggleButton(Thingy):
    """Concrete class referring to physical button on Nocturn."""
    minValue = 0
    maxValue = 1
    pressValue = 127

    def __init__(self, surface, address, number):
        super(ToggleButton, self).__init__(surface,address)
        self.LEDAddress = chr(0x70 + number-1)
    # Turns button LED on or off
    # val = 0 or 1
    def setLED(self, val):
        if ((val == 0) | (val == 1)):
            self.surface.getUsber().write(self.LEDAddress + chr(val))
            return

        raise NameError("Button value needs to be 0 or 1")

    def setValue(self, value):
        super(ToggleButton, self).setValue(value)
        self.setLED(value)

    def instruct(self, val):
        if (val == ToggleButton.pressValue):
            self.setValue(ToggleButton.maxValue-self.value)
        super(ToggleButton, self).instruct(self.value*ToggleButton.pressValue)

class Midder(object):
    """Virtualization layer for Midi communication."""

    CC_OFFSET = 0xb0
    
    def __init__(self, confData):
        self.inDev = confData[0]
        self.outDev = confData[1]
        self.latency = confData[2]
        
        #Initialize pypm - I'm told bad things will happen otherwise
        pypm.Initialize()
        self.MidiOut = pypm.Output(self.outDev,self.latency)
        self.MidiIn = pypm.Input(self.inDev)
        
    def send(self,channel,cc, val):
        self.MidiOut.WriteShort(Midder.CC_OFFSET+channel,cc,val)
    def recv(self):
        pass

class Usber(object):
    """Virtualization layer for USB communication."""
    
    vendorID = None
    productID = None
    initPackets = None
    
    def __init__(self, confData):
        
        self.vendorID = confData[0]
        self.productID = confData[1]
        self.initPackets = confData[2]
        
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
            sys.exit('Something is wrong with your USB setup - check udev ' +
                     'rules, perhaps?')

        # init routine - packet meaning unknown, reverse-engineered
        for packet in self.initPackets:
            self.ep.write(binascii.unhexlify(packet))
    
    
    def write(self, packet):
        self.ep.write(packet)
        
    def read(self):
        try:
            data = self.ep2.read(self.ep2.wMaxPacketSize,10)
            return data
        except usb.core.USBError:
            return None
                
class PageContainer(object):
    """Contains virtual pages for Nocturn."""
    
    
    def __init__(self,surface,configurator):
        self.currentPage = 0
        self.pages = []
        
        pageData = configurator.getPageSettings()
        while pageData != None:
            self.pages.append(Page(surface,pageData))
            pageData = configurator.getPageSettings()
    
    def getCurrentPage(self):
        print "Returning page {}".format(self.currentPage)
        return self.pages[self.currentPage]
        

class Page(object):
    """Contains virtual encoders, buttons."""
    
    
    def __init__(self,surface, pageData):
        
        self.encoders = []
        self.buttons = []
        # recall that we can count on pageData to be in order
        for i, encoder in enumerate(pageData['encoders']):
            self.encoders.append(ControlUnit(surface, encoder,
                                      surface.getThingy('encoder', i)))
        for i, button in enumerate(pageData['buttons']):
            self.buttons.append(ControlUnit(surface,
                                button,surface.getThingy('button',i)))
    
    def getControlUnit(self, type, num):
        if type == 'encoder':
            return self.encoders[num]
        elif type == 'button':
            return self.buttons[num]
        else:
            return None
    
    
class ControlUnit(object):
    """Virtual representation of a control unit on a page.
    Has action and response."""
    
    def __init__(self, surface, cuData, physical):
        self.action = []
        self.value = 0
        
        if cuData[0] == 'midi':
            self.action.append(MidiWriter(surface, int(cuData[1]),
                                          int(cuData[2])))
        self.physical = physical
    
    def setValue(self, value):
        self.value = value
    
    def act(self, value):
        for action in self.action:
            action.act(value)
        self.setValue(value)

class CUAction(object):
    """Abstract class for action for a control unit. Would be something like a
    MIDI writer or a keypress generator."""

class MidiWriter(CUAction):
    """Concrete class - MIDI writer.
    Requires a Surface with a Midder to write to."""
    
    def __init__(self, surface, channel, cc):
        self.channel = channel-1
        self.cc = cc-1
        self.surface = surface
    
    def act(self, value):
        print "Sending MIDI signal {} to cc {} on channel {}".format(value,self.cc,self.channel)
        self.surface.getMidder().send(self.channel,self.cc,value)

class KeyGenerator(CUAction):
    """Future implementation, will allow keypresses
    to be generated as an action."""
    
class CUResponse(object):
    """Abstract class for response on a control unit. Requires reference to
    physical device for display, or could be a dummy for the slider.
    Could also exercise programmatic control, such as switching the current
    page or running a command."""

class DummyResponse(CUResponse):
    """Does nothing."""

class Lighter(CUResponse):
    """Lights the LED ring on the physical control unit.
    Needs reference to physical control unit."""
    
class Pager(CUResponse):
    """Changes the Nocturn page. Can be set to increment or decrement
    current page, or go to a specific page."""

######

nocturn = Nocturn()
nocturn.run()