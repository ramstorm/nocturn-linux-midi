#!/usr/bin/python2

try:
    import pypm
except ImportError:
    from pygame import pypm

DEBUG = False

class Midder(object):
    """Virtualization layer for Midi communication."""

    NOTE_OFF_OFFSET = 0x80
    NOTE_ON_OFFSET = 0x90
    CC_OFFSET = 0xb0
    
    def __init__(self, inDev, outDev, latency=5, channel=0):
        self.inDev = inDev
        self.outDev = outDev
        self.latency = latency
        self.channel = channel
        
        #Initialize pypm - I'm told bad things will happen otherwise
        pypm.Initialize()
        self.MidiOut = pypm.Output(self.outDev,self.latency)
        #self.MidiIn = pypm.Input(self.inDev)
        
    def send(self, cc, msg, val):
        try:
            offset = Midder.CC_OFFSET
            if msg == 'NOTE':
                offset = Midder.NOTE_ON_OFFSET if val > 0 else Midder.NOTE_OFF_OFFSET
            if DEBUG:
                print ("writing midi message " + str(offset+self.channel) + " " +
                        str(cc) + " " + str(val))
            self.MidiOut.WriteShort(offset+self.channel,cc,val)
        except Exception as e:
            print type(e)
            print e.args
            print e
    def recv(self, data):
        # MIDI input is disabled
        #data = self.MidiIn.Read(1)
        if data != [] and not (data[0][0][0] < 0xb0 or data[0][0][0] > 0xbf):
            return [data[0][0][0]-Midder.CC_OFFSET,data[0][0][1],data[0][0][2]]
        else:
            return None
    
    def setChannel( self, channel ):
        self.channel = channel

midder = Midder( 1, 0 )

def getMidder( ):
    return midder
