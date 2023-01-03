#!/usr/bin/python2

from NocturnHardware import NocturnHardware

import sys

DEBUG = False

# Clarification of terminology:
# surface: as in MIDI control surface - the Nocturn is an example of this
# controller: one of the knobs or buttons or the slider
# knob, button, slider: just look at the hardware - you'll understand

# Using M-V-C
# First, defining the model

class NocturnModel( object ):
    """Contains current state of a virtual representation of the Nocturn."""
    
    # The Nocturn doesn't (as far as I know) have an internal representation of
    # the state of its controllers.
    
    def __init__( self ):
        # The list of virtual pages of controllers
        # Pages are instances of the NocturnPage class
        self.pages = []
        self.observers = []
        self.activePage = None
        self.hardware = NocturnHardware()
        self.permaBar = PermaBar( self )
        
    def addPage( self, page ):
        activate = False
        if self.pages == []:
            activate = True
        self.pages.append( page )
        if activate:
            self.setActivePage(0)
            activate = False

    def delPage( self, page ):
        pass
    
    def incPage( self, inc ):
        """Increments the active page by inc"""
        page = self.activePage + inc
        if page < len( self.pages ) and page >= 0:
            self.setActivePage( page )
        return ( self.activePage == len( self.pages ) - 1 )
    
    def getPage( self, page ):
        return self.pages[page]
        
    def getActivePage( self ):
        """Returns pointer to actual active page, not just number"""
        return self.pages[self.activePage]
            
    def setActivePage( self, page ):
        self.activePage = page
        self.getActivePage().setAllChanged()
        self.notifyObservers()
    
    def getNumPages( self ):
        return len(self.pages)
    
    def getValue( self, page, controller ):
        return self.pages[page].getController( controller ).getValue()
    
    def registerObserver( self, observer ):
        self.observers.append( observer )
        # Observers must have notify(), which is called by NocturnModel when
        # its state changes
    
    def notifyObservers( self ):
        self.update()
        for obs in self.observers:
            obs.notify()
            
    def set( self, page, controller, value ):
        theController = self.pages[page].getController(controller)
        theController.set(value)
    
    def setPerma( self, controller, value ):
        theController = self.permaBar.getController( controller )
        theController.set( value )
    
    def getPerma( self ):
        return self.permaBar
    
    def setAction( self, page, controller, action ):
        self.getPage( page ).getControllers()[ controller ].setAction( action )
        
    def setPermaAction( self, perma, action ):
        self.permaBar.getControllers()[ perma ].setAction( action )
    
    def update( self ):
        """Updates the hardware lights with stored values, but only sends
        codes if NocturnController.isChanged()"""
        for cc in self.getActivePage().getEncoders():
            if cc.isChanged():
                val = cc.getValue()
                try:
                    self.hardware.setLEDRingValue( cc.getNumber(), val )
                except Exception as e:
                    sys.exit(e)
                cc.notifyDone()
        for cc in self.getActivePage().getButtons():
            if cc.isChanged():
                val = cc.getValue()
                try:
                    self.hardware.setButton( cc.getNumber(), val )
                except Exception as e:
                    sys.exit(e)
            cc.notifyDone()
        for cc in self.permaBar.getButtons():
            if cc.isChanged():
                val = cc.getValue()
                try:
                    self.hardware.setButton( cc.getNumber() + 8, val )
                except Exception as e:
                    print str(e)
            cc.notifyDone()
        for cc in self.permaBar.getEncoders():
            if cc.isChanged():
                val = cc.getValue()
                try:
                    self.hardware.setLEDRingValue( cc.getNumber(), val )
                except Exception as e:
                    print str(e)
            cc.notifyDone()
    
    def poll( self ):
        """Read from hardware, once. Simply returns if there is no data. Data
        truncated to one message. If messages are piling up, you're doing it
        wrong."""
        data = self.hardware.processedRead()
        if data is None:
            return
        mappedController = self.getActivePage().hwMap.get( data[0] )
        if mappedController:
            pass
        else:
            mappedController = self.permaBar.hwMap.get( data[0] )
        if mappedController:
            mappedController.act( data[1] )
    def disconnect( self ):
        self.hardware.clearAll()

class NocturnView( object ):
    
    def __init__( self, subject ):
        self.subject = subject
    
    def notify( self ):
        pass

class ControllerCollection( object ):
    def __init__( self, surface):
        
        self.surface = surface
        self.hwMap = dict()
        
        # List of all the controllers on the page.
        self.controllers = []
        self.buttons = []
        self.encoders = []
        self.sliders = []
        
    def getSurface( self ):
        return self.surface
    
    def getController( self, number ):
        return self.controllers[number]

    def getControllers( self ):
        return self.controllers
    
    def getButtons( self ):
        return self.buttons
    
    def getSliders( self ):
        return self.sliders
    
    def getEncoders( self ):
        return self.encoders
    
    def numControllers( self ):
        return len(self.controllers)
    
    def notifyObservers( self ):
        self.surface.notifyObservers()
        for cc in self.controllers:
            cc.notifyDone()
    
    def setAllChanged( self ):
        for controller in self.controllers:
            controller.setChanged()

class NocturnPage( ControllerCollection ):
    """A virtual page of controllers."""
    
    # Each page must have exactly 1 slider, 8 encoders, 8 buttons
    # These can be added statically, since the Nocturn model is unlikely
    # to be used elsewhere. If this project becomes a complete clone of
    # Automap, the model will have to be abstracted, but for now, this way
    # is simpler.
    # Presently, I'm ignoring the speed dial until I find a good use for it.
    
    numSlider = 1
    numEncoder = 8
    numButton = 8
    
    def __init__( self, surface):
        super( NocturnPage, self ).__init__( surface )
        
        # Lists of individual controller types        
        
        for ii in range( NocturnPage.numEncoder ):
            ee = NocturnEncoder( self,  ii)
            self.encoders.append( ee )
            self.controllers.append( ee )
        for ii in range( NocturnPage.numButton ):
            bb = NocturnButton( self, ii)
            self.buttons.append( bb )
            self.controllers.append( bb )
        for ii in range( NocturnPage.numSlider ):
            ss = NocturnSlider( self, ii)
            self.sliders.append( ss )
            self.controllers.append( ss )
        
        buttonIter = iter(self.buttons)
        for ii in range ( 112, 120 ):
            self.hwMap[ii] = buttonIter.next()
        
        encoderIter = iter(self.encoders)
        for ii in range ( 64, 72 ):
            self.hwMap[ii] = encoderIter.next()


class PermaBar( ControllerCollection ):
    numButton = 8
    
    def __init__( self, surface):
        super( PermaBar, self ).__init__( surface )
        
        for ii in range( PermaBar.numButton ):
            bb = NocturnButton( self, ii)
            self.controllers.append( bb )
            self.buttons.append( bb )
        
        buttonIter = iter(self.controllers)
        for ii in range ( 120, 128 ):
            self.hwMap[ii] = buttonIter.next()
            
        theSpeedDial = NocturnEncoder( self, PermaBar.numButton )
        self.controllers.append( theSpeedDial )
        self.encoders.append( theSpeedDial )
        self.hwMap[74] = theSpeedDial
        
        theSlider = NocturnSlider( self, PermaBar.numButton + 1)
        self.controllers.append( theSlider )
        self.sliders.append( theSlider )
        self.hwMap[72] = theSlider

class NocturnController( object ):
    
    def __init__( self, page, label ):
        self.value = 0
        self.page = page
        self.label = label
        self.changed = False
    
    def set( self, value ):
        self.value = value
        self.changed = True
        self.page.notifyObservers()
    
    def increment( self, value ):
        self.set(self.value + value)
    
    def getValue( self ):
        return self.value
    
    def getNumber( self ):
        return self.label
    
    def getPage( self ):
        return self.page
    
    def setChanged( self ):
        self.changed = True
    
    def isChanged( self ):
        return self.changed
    
    def notifyDone( self ):
        self.changed = False
    
    def setAction( self, action ):
        self.action = action
        self.action.setParent( self )
    
    def getAction( self ):
        """Oh yeah baby."""
        return self.action
    
    def act( self, value ):
        try:
            self.action.execute( value )
        except:
            pass
        
        
class NocturnButton( NocturnController ):
    
    def __init__( self, page, label ):
        super( NocturnButton, self ).__init__( page, label )
    
    def getLabel( self ):
        return( "Button " + str(self.label) )
    
    def set( self, value ):
        value = 1 if value == 127 or value == 1 else 0
        super( NocturnButton, self ).set( value )
    
    def act( self, value ):
        #print ("Button act " + str(value))
        #if value != 0:
        #    value = 0 if self.value == 1 else 127
        super( NocturnButton, self).act( value )
    
class NocturnEncoder( NocturnController ):
    
    # The sensitivity. Would probably be weird to change it, since degrees of
    # rotation should equal degrees of lit LEDs, but go nuts!
    SENS = 3
    
    
    def __init__( self, surface, label ):
        super( NocturnEncoder, self ).__init__( surface, label )
    
    def getLabel( self ):
        """Deprecated"""
        return( "Encoder " + str(self.label) )
    
    def act( self, value, absolute=False):
        if not absolute:
            value = value if value < 64 else 0 - ( 128 - value )
            value *= NocturnEncoder.SENS
            value = self.value + value
            value = 0 if value < 0 else value
            value = 127 if value > 127 else value
        super( NocturnEncoder, self ).act( value )

class NocturnSlider( NocturnController ):
    
    def __init__( self, surface, label ):
        super( NocturnSlider, self ).__init__( surface, label )
    
#    def set( self, value ):
#        pass
    
    def getLabel( self ):
        """Deprecated"""
        return( "Slider " + str(self.label) )
