#!/usr/bin/python2

import pypm

class Midder(object):
    """Virtualization layer for Midi communication."""

    CC_OFFSET = 0xb0
    
    def __init__(self, inDev, outDev, latency=5, channel=0):
        self.inDev = inDev
        self.outDev = outDev
        self.latency = latency
        self.channel = channel
        
        #Initialize pypm - I'm told bad things will happen otherwise
        pypm.Initialize()
        self.MidiOut = pypm.Output(self.outDev,self.latency)
        self.MidiIn = pypm.Input(self.inDev)
        
    def send(self,cc, val):
        print "midder attempting write"
        try:
            self.MidiOut.WriteShort(Midder.CC_OFFSET+self.channel,cc,val)
        except Exception as e:
            print type(e)
            print e.args
            print e
    def recv(self):
        data = self.MidiIn.Read(1)
        if data != [] and not (data[0][0][0] < 0xb0 or data[0][0][0] > 0xbf):
            return [data[0][0][0]-Midder.CC_OFFSET,data[0][0][1],data[0][0][2]]
        else:
            return None
    
    def setChannel( self, channel ):
        self.channel = channel

midder = Midder( 1, 0 )

def getMidder( ):
    return midder