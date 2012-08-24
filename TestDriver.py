#!/usr/bin/python2

# Standard stuff to import
import array
import sys
import time

from NocturnModel import *
from NocturnHardware import *
from NocturnActions import *

class TestNocturnView( NocturnView ):
    def __init__( self, subject ):
        super( TestNocturnView, self ).__init__( subject )
        self.numPages = 0
    
    def notify( self ):
        numPages = self.subject.getNumPages()
        for pp in range( numPages ):
            curPage = nocturn.getPage( pp ) 
            for cc in range( curPage.numControllers() ):
                pass
                #print("Page %s %s : %s" % (pp, curPage.getController( cc ).getLabel(), nocturn.getValue( pp, cc ) ) )

nocturn = NocturnModel()

testView = TestNocturnView( nocturn )
nocturn.registerObserver( testView )

for ii in range (0,6):
    newPage = NocturnPage( nocturn )
    for controller in newPage.getControllers():
        ma = MIDIAction()
        ma.setMIDICommand( ii )
        controller.setAction( ma )
    nocturn.addPage( newPage )

nocturn.setActivePage( 0 )

nocturn.setPermaAction( 3, PagerAction( 1 ) )
nocturn.setPermaAction( 2, PagerAction( -1 ) )


while( True ):
    nocturn.poll()