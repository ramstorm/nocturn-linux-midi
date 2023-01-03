#!/usr/bin/python2

# Configurator.py

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

#import pprint
from NocturnModel import NocturnModel, NocturnPage
from NocturnActions import PagerAction, MIDIAction
import Midder

class Configurator( object ):
    pag = 'Pag'
    but = 'But'
    enc = 'Enc'
    sli = 'Sli'
    
    
    def __init__( self, configFile ):
        self.file = None
        #~ try:
        self.file = self._openFile( configFile )
        #~ except Exception:
            #~ print "File read
            #~ return
        
        #~ self.pp = pprint.PrettyPrinter( indent = 4 )
    
    def __del__( self ):
        self.file.close()
    
    def progToFile( self, nocturn ):
        self.nocturn = nocturn
        self._serialize()
    
    def fileToProg( self, nocturn ):
        self.nocturn = nocturn
        self._parseFile()
        return self.nocturn
    
    def _openFile( self, configFile ):
        return open( configFile, 'r+b' )
    
    def _parseFile( self ):
        pass
    
    def _serialize( self ):
        pass
        
class YAMLConfigurator( Configurator ):
    def __init__( self, configFile ):
        super( YAMLConfigurator, self ).__init__( configFile )
    
    def _parseFile( self ):
        if self.file:
            data = load( self.file )
            #~ self.pp.pprint(data)
            pag = Configurator.pag
            but = Configurator.but
            enc = Configurator.enc
            sli = Configurator.sli
            ii = 0
            while ( pag + str(ii) ) in data:
                curPage = data[ pag + str(ii) ]
                self.nocturn.addPage( NocturnPage( self.nocturn ) )
                for jj in range(8):
                    if ( but + str(jj) ) in curPage:
                        curBut = curPage[ but + str(jj) ]
                        
                        self.nocturn.setAction( ii, jj + 8,
                            self._genAction(curBut['Action'],
                                curBut['Data']) )
                
                for jj in range(8):
                    if ( enc + str(jj) ) in curPage:
                        curEnc = curPage[ enc + str(jj) ]
                        
                        self.nocturn.setAction( ii, jj,
                            self._genAction(curEnc['Action'],
                                curEnc['Data']) )
                ii += 1
            pb = data[ 'PermaBar' ]
            for jj in range(8):
                    if ( but + str(jj) ) in pb:
                        curBut = pb[ but + str(jj) ]
                        
                        self.nocturn.setPermaAction( jj,
                            self._genAction(curBut['Action'],
                                curBut['Data']) )
            if ( sli + str(0) ) in pb:
                curSli = pb[ sli + str(0) ]
                
                self.nocturn.setPermaAction ( 8, self._genAction(curSli[ 'Action' ],
                                                               curSli[ 'Data' ]) )
            if ( enc + str(0) ) in pb:
                curEnc = pb[ enc + str(0) ]
                
                self.nocturn.setPermaAction ( 9, self._genAction( curEnc[ 'Action' ],
                                                                  curEnc[ 'Data' ]) )
    def _genAction( self, actType, data ):
        action = None
        if actType == 'MIDI' or actType == 'MIDI-NOTE':
            action = MIDIAction()
            action.setMIDIMessage( 'NOTE' if actType == 'MIDI-NOTE' else 'CC' )
            action.setMIDICommand( data )
            action.setMidder( Midder.getMidder() )
        elif actType == 'PAGE':
            action = PagerAction( data )
        return action
    
    #~ def _serialize( self ):
        #~ sd = dict()
        #~ pag = 1
        #~ for page in self.state.pages:
            #~ pagID = 'Pag' + str(pag)
            #~ sd[ pagID ] = dict()
            #~ typID = "Enc"
            #~ enc = 1
            #~ for encoder in page.encoders:
               
            #~ pag += 1

if __name__ == "__main__":
    print "name is main!"
    config = YAMLConfigurator( "test.yaml" )
    nocturn = NocturnModel()
    config.fileToProg( nocturn )
    
    while True:
        nocturn.poll()
