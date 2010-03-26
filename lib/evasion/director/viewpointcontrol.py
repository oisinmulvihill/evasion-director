"""
This module provides an interface to the XUL control viewpoint.
This version of the viewpoint is on the message bus and is 
controlled via events. To hide some of the complexity involved
and provide a series of easy to use functions, similar to those
available in the viewpoint direct module.

Oisin Mulvihill
2009-11-05

"""
import logging

from evasion import messenger


class BrowserCalls(object):
    """This instructs the browser to act on instructions via the message bus.
    
    This class is used in conjection with the 'viewpointxulcontrol'.
    This module is the 'other side' of the message bus and sets up
    the event handlers we send to.
    
    """
    def __init__(self):
        self.log = logging.getLogger("evasion.director.viewpointcontrol.BrowserCalls")
  
  
    def getBrowserUri(self):
        """Called to recover where the viewpoint browser is looking currently.
        
        This method sends the VIEWPOINT_GET_URI event and 
        returns its response.
        
        """
        evt = messenger.EVT("VIEWPOINT_GET_URI")
        
        resp = messenger.eventutils.send_await(evt)
            
        self.log.info("getBrowserUri: returned '%s'." % (resp))
            
        return resp

    
    def setBrowserUri(self, uri):
        """Called to the viewpoint browser which URI to load.
        
        This method sends the VIEWPOINT_SET_URI event along
        with the new_uri and returns its response.
        
        """
        evt = messenger.EVT("VIEWPOINT_SET_URI")
        
        self.log.debug("setBrowserUri: sending new uri '%s'." % (uri))

        resp = messenger.eventutils.send_await(evt, dict(uri=uri))
            
        self.log.info("setBrowserUri: returned '%s'." % (resp))
            
        return resp

    
    def replaceContent(self, content_id, content):
        """Called to replace content inside the viewpoint browser with
        the given content fragment.
        
        This method sends the VIEWPOINT_REPLACE event along
        with the content_id & content returning its response.

        """
        evt = messenger.EVT("VIEWPOINT_REPLACE")
        
        self.log.debug("replaceContent: replacing content_id '%s'." % (content_id))

        resp = messenger.eventutils.send_await(
            evt, 
            dict(content_id=content_id, content=content)
        )
            
        self.log.info("replaceContent: returned '%s'." % (resp))
            
        return resp

    
    def viewpointQuit(self):
        """
        Called to instruct the viewpoint to close and exit normally.
        
        This method sends the VIEWPOINT_QUIT event.

        """
        evt = messenger.EVT("VIEWPOINT_QUIT")
        
        self.log.debug("viewpointQuit: instructing viewpoint to quit.")
        resp = messenger.eventutils.send_await(evt)
            
        return resp

