import ConfigParser

class Configurator(object):
    """Provides values from configuration file."""

    def __init__(self, file):
        self.config = ConfigParser.ConfigParser()
        self.config.read(file)
        self.nextPage = 1
        self.maxPages = self.config.getint('Pages','number')
        
    def reconfigure(self):
        pass
    
    def getUSBSettings(self):
        vendorID = int(self.config.get('USB', 'vendorID'),0)
        productID = int(self.config.get('USB', 'productID'),0)
        initPackets= self.config.get('USB', 'initPackets').split()
        return [vendorID, productID, initPackets]
    
    def getMIDISettings(self):
        inDev = self.config.getint('MIDI', 'inDev')
        outDev = self.config.getint('MIDI', 'outDev')
        latency = self.config.getint('MIDI', 'latency')
        return [inDev, outDev, latency]
        
    def getPageSettings(self):
        if self.nextPage > self.maxPages:
            self.nextPage = 1
            return None
        
        numEncoders = 9
        #implies encoders from 0 to 8, 0 being 'speed dial'
        
        nextPageData = dict()
        pageSection = 'Page{!s}'.format(self.nextPage)
        
        encoders = []
        for i in xrange(numEncoders):
            thisEncoder = []
            try:
                mode = self.config.get(pageSection,'Encoder{}Mode'.format(i))
            except ConfigParser.NoOptionError:
                mode = self.config.get(pageSection,'defaultMode')
                
            thisEncoder.append(mode)
            
            if thisEncoder[0] == 'midi':
                try:
                    channel = self.config.get(pageSection,'Encoder{}Channel'.format(i))
                except ConfigParser.NoOptionError:
                    channel = self.config.get(pageSection,'defaultChannel')
                
                thisEncoder.append(channel)
                
                thisEncoder.append(self.config.get(pageSection,'Encoder{}Controller'.format(i)))
            
            else:
                for j in range(2):
                    print j
                    thisEncoder.append(0)
            
            encoders.append(thisEncoder)
        nextPageData['encoders'] = encoders
        
        self.nextPage = self.nextPage + 1
        return nextPageData