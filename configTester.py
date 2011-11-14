from configurator import *

# A tester driver for the configurator - not useful for you

testConfig = Configurator('default.conf')

print testConfig.getUSBSettings()
print testConfig.getMIDISettings()

testConfig.getPageSettings()
