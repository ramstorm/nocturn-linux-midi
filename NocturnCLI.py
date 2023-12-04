#!/usr/bin/python2

import threading
import sys
import signal

from pubsub import pub
from Configurator import YAMLConfigurator
import Midder
from NocturnModel import NocturnModel
from optparse import OptionParser


class CLINocturnModel( NocturnModel ):
    def notifyObservers( self ):
        self.update()

class PollThread( threading.Thread ):
    
    def __init__( self, configFile ):
        super( PollThread, self ).__init__()
        config = YAMLConfigurator( configFile )
        
        self.nocturn = CLINocturnModel()
        self.midder = Midder.getMidder()
        config.fileToProg( self.nocturn )
        
        self._stop = False
        
        #self.start()
    
    def run( self ):        
        
        while( not self._stop ):
            self.nocturn.poll()
            self.nocturn.led()

    def stop( self ):
        self._stop = True

    def getNocturn( self ):
        return self.nocturn


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="configuration file", metavar="FILE")
    (options, args) = parser.parse_args()
    try:
        thread = PollThread( options.filename )
        thread.start()
        signal.pause()
    except KeyboardInterrupt:
        print "KBInterrupt received, exiting..."
        thread.stop()
        sys.exit()

