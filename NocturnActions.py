#!/usr/bin/python2

from pubsub import pub

DEBUG = False

class ChannelAction( object ):
    
    def __init__( self ):
        pass
    
    def execute( self ):
        pass
        
    def setParent( self, parent ):
        self.parentController = parent
    
class MIDIAction( ChannelAction ):
    
    def __init__( self ):
        super( MIDIAction, self ).__init__( )
        self.MIDIChannel = 0
        self.MIDIMessage = 'CC'
        self.MIDICommand = 0
        self.midder = None
    
    def setMIDICommand( self, CC ):
        self.MIDICommand = CC

    def setMIDIMessage( self, msg ):
        self.MIDIMessage = msg

    def setMidder( self, midder ):
        self.midder = midder
    
    def execute( self, value ):
        if DEBUG:
            print "Sending MIDI CC %d with value %d" % \
                ( self.MIDICommand, value )
        self.midder.send( self.MIDICommand, self.MIDIMessage, value )
        self.parentController.set( value )
    
    def MIDIListener( self, channel, cc, value ):
        if cc == self.MIDICommand:
            if DEBUG:
                print "that's me, MIDI controller", str(self.MIDICommand)
            self.parentController.set( value )
    
    def __str__( self ):
        return "MIDI Action - CC " + str( self.MIDICommand )

class PagerAction( ChannelAction ):
    pagerActions = []
    
    def __init__( self, inc ):
        super( PagerAction, self ).__init__( )
        self.inc = inc
        PagerAction.pagerActions.append( self )
    
    def execute( self, value ):
        if value == 0:
            return # ignore button release

        surface = self.parentController.getPage().getSurface()
        surface.incPage( self.inc )
        
        for item in PagerAction.pagerActions:
            item.update()
        
        nextActivePage = surface.activePage + self.inc
    
    def update( self ):
        surface = self.parentController.getPage().getSurface()
        nextActivePage = surface.activePage + self.inc
        
        if ( nextActivePage >= surface.getNumPages() ) or ( nextActivePage < 0 ):
            self.parentController.set( 0 )
        else:
            self.parentController.set( 127 )
    
    def __str__( self ):
        return "Pager Action - Increment by " + str( self.inc )
