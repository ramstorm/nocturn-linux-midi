#!/usr/bin/python2

# NocturnGUI.py

import wx
import threading
import sys

from NocturnModel import *
from NocturnHardware import *
from NocturnActions import *
from Configurator import *

class GUINocturnModel( NocturnModel ):
    """Must be used with wxPython, because NocturnModel calls obs.notify()
    directly. This causes horrible lag/missed messages."""
    def notifyObservers( self ):
        self.update()
        for obs in self.observers:
            wx.CallAfter( obs.notify )

class ControllerActionWindow( wx.Dialog ):
    """Dialog for right-click on controllers. This will eventually allow
    selection of new actions, but for now, shows the current action."""
    def __init__(self, parent, controller ):
        super(ControllerActionWindow, self).__init__( parent ) 
        
        self.controller = controller
        self.InitUI()
        self.SetSize((300, 100))
        self.SetTitle("Action - " + str(controller) )
        
        self.Bind( wx.EVT_CLOSE, self.OnClose )
    
    def InitUI( self ):
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( wx.StaticText( self, -1, "Action type:" ) )
        vbox.Add( wx.StaticText( self, -1, str( self.controller.getAction() ) ) )
        
        self.SetSizer( vbox )
    
    def OnClose( self, e ):
        self.Destroy()

class NGUIControl( wx.Control ):
    def __init__( self ):
        pass
    
    def OnMouse( self,  e ):
        """Ctrl-click or right-click will bring up a dialog about the action
        of the controller"""
        if ( self._mouseDeal( e ) ):
            return
        else:
            e.Skip()
    
    def OnUpdate( self, event=None ):
        self.controller.act( self.GetValue(), True )

    def setController( self, controller ):
        self.controller = controller

    def getController( self ):
        return self.controller
    
    def _mouseDeal( self, e ):
        if ( e.CmdDown() and e.LeftDown() ) or e.RightDown():
            aw = ControllerActionWindow( self, self.getController() )
            aw.ShowModal()
            return True
        return False
    

class EncoderSlider( wx.Slider, NGUIControl ):
    def __init__( self, parent ):
        super( EncoderSlider, self ).__init__( parent, -1, 0, 0, 127,
            style = wx.SL_AUTOTICKS | wx.SL_VERTICAL | wx.SL_LABELS | wx.SL_INVERSE )
        self.Bind( wx.EVT_MOUSE_EVENTS, self.OnMouse )
        self.Bind( wx.EVT_SLIDER, self.OnUpdate )
        self.controller = None

class ButtonButton( wx.ToggleButton, NGUIControl ):
    def __init__(self, parent, id, label ):
        super( ButtonButton, self ).__init__( parent, id, label )
        self.Bind( wx.EVT_MOUSE_EVENTS, self.OnMouse )
    
    def setController( self, controller ):
        self.controller = controller
    
    def OnMouse( self, e ):
        if ( self._mouseDeal( e ) ):
            return
        elif ( e.LeftDown() ):
            self.controller.act( 127 )
        else:
            e.Skip()
    
    def getController( self ):
        return self.controller

class NocturnFrame(wx.Frame):
    def __init__(self, parent, id, title ):
        
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition)
        
        self.sliders = []
        
        fd = wx.FileDialog( None, message = "Select your configuration file..." )
        fd.ShowModal()
        
        configFile = fd.GetPath()
        print configFile
        
        self.pollThread = PollThread( configFile )
        
        self.nocturn = self.pollThread.getNocturn()
        self.nocturn.registerObserver( self )
        
        sizer = wx.GridBagSizer(10, 12)
        
        for ii in range (8):
            self.sliders.append( EncoderSlider( self ) )
        
        for ii in range( 4 ):
            sizer.Add( self.sliders[ii], (0,ii), (5,1), wx.EXPAND )
            sizer.AddGrowableCol( ii )
        
        sizer.Add( wx.Slider(self, -1, 0, 0, 127,
            style = wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS ),
            (6,4), (1,4), wx.EXPAND )
        sizer.AddGrowableCol(4)
        
        for ii in range( 8, 12 ):
            sizer.Add( self.sliders[ii-4], (0,ii), (5,1), wx.EXPAND  )
            sizer.AddGrowableCol( ii )
        
        self.buttons = []
        for ii in range( 8 ):
            self.buttons.append( ButtonButton( self, -1, str(ii+1) ) )
        
        for ii in range( 4 ):
            sizer.Add( self.buttons[ii],
                (7,ii), (1,1), wx.EXPAND )
        
        for ii in range ( 8, 12 ):
            sizer.Add( self.buttons[ii-4],
                (7,ii), (1,1), wx.EXPAND )

        labels = [ "learn", "view", "page -", "page +",
            "user", "fx", "inst", "mixer" ]
        self.permaButtons = []
        for ii in range( 8 ):
            self.permaButtons.append( ButtonButton( self, -1, labels[ii] ) )
            
        for ii in range ( 4 ):
            sizer.Add( self.permaButtons[ii],
                (8,ii), (1,1), wx.EXPAND )
        
        for ii in range ( 8, 12 ):
            sizer.Add( self.permaButtons[ii-4],
                (8,ii), (1,1), wx.EXPAND )
        
        sizer.AddGrowableRow(0)

        self.SetSizerAndFit(sizer)
        
        self.Centre()
        self.Bind(wx.EVT_CLOSE, self._when_closed)
        self.notify()

    def _when_closed(self, event):
        self.pollThread.stop()
        event.Skip()
    
    def getSliders( self ):
        return self.sliders
    
    def getButtons( self ):
        return self.buttons
    
    def getPermaButtons( self ):
        return self.permaButtons
    
    def notify( self ):
        page = self.nocturn.getActivePage()
        sliders = self.getSliders()
        buttons = self.getButtons()
        permaButtons = self.getPermaButtons()
        
        encoders = page.getEncoders()
        for ii in range( len(sliders) ):
            sliders[ii].SetValue( encoders[ii].getValue() )
            sliders[ii].setController( encoders[ii] )
        
        nButtons = page.getButtons()
        for ii in range( len(buttons) ):
            buttons[ii].SetValue( nButtons[ii].getValue() )
            buttons[ii].setController( nButtons[ii] )
        
        pButtons = self.nocturn.getPerma().getButtons()
        for ii in range( len(permaButtons) ):
            permaButtons[ii].SetValue( pButtons[ii].getValue() )
            permaButtons[ii].setController( pButtons[ii] )

class NocturnGUI(wx.App):
    
    def __init__( self, redirect ):
        super( NocturnGUI, self ).__init__(redirect)

    
    def OnInit( self ):
        self.frame = NocturnFrame(None, -1, "Novation Nocturn Controller" )
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
        

    
    
    

#****************************************#


# lock = threading.Lock()

class PollThread( threading.Thread ):
    
    def __init__( self, configFile ):
        super( PollThread, self ).__init__()
        config = YAMLConfigurator( configFile )
        
        self.nocturn = GUINocturnModel()
        self.midder = Midder.getMidder()
        config.fileToProg( self.nocturn )
        
        self._stop = False
        
        self.start()
    
    def run( self ):        
        
        try:
            while( not self._stop ):
                self.nocturn.poll()
                midi = self.midder.recv()
                if midi:
                    pub.sendMessage( 'MIDI_IN_MESSAGES', channel=midi[0],
                            cc=midi[1], value=midi[2] )
        except KeyboardInterrupt:
            print "KBInterrupt received, exiting..."
            sys.exit()
    
    def stop( self ):
        self._stop = True
    
    def getNocturn( self ):
        return self.nocturn


if __name__ == "__main__":
    app = NocturnGUI( 0 )
    app.MainLoop()