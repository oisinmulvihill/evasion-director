"""
:mod:`viewpointpassive` -- This doesn't start a viewpoint but controls one if runnning.
=========================================================================================

.. module:: evasion.director.controllers.viewpointpassive
   :platform: Unix, MacOSX, Windows
   :synopsis: This doesn't start a viewpoint but controls one if runnning.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: evasion.director.controllers.viewpointctrl.Controller
   :members:
   :undoc-members:
   
.. autofunction:: evasion.director.controllers.dump
   
.. autofunction:: evasion.director.controllers.load


"""
import os
import socket
import logging
import subprocess
import pkg_resources

import simplejson
from pydispatch import dispatcher

from evasion import agency
from evasion import director
from evasion import messenger
from evasion.director.tools import net
from evasion.director import viewpointdirect
from evasion.director.controllers import viewpoint



def get_log():
    return logging.getLogger("evasion.director.controllers.viewpointxulcontrol")



def dump(control_frame):
    """This takes a control frame dict or other data 
    structure. It converts it to a javascript compatible 
    data type. Finally this is then quoted ready for 
    transmission.
    
    """
    control_frame = simplejson.dumps(control_frame)
    return control_frame


def load(message):
    """This takes a message string returned from the remote
    XUL Browser command. It unquotes it and then attemts to
    load the returned data structure.
    
    """
    message = simplejson.loads(message)
    return message


class Controller(viewpoint.Controller):
    """
    This controller plugs the XUL Control protocol
    into the message bus.
    
    This controller typically has the following configuration::

        [viewpointxulcontrol]
        disabled = 'no'
        order = 1
        controller = 'director.controllers.viewpointxulcontrol'

        # Disable 
        
        # The URI to connect to when the URI is present and the viewpoint
        # is ready to recieve requests. The viewpoint will also be kept
        # looking at this URI so it can't navigate away out of the app.
        uri = "http://myhost:myport/myapp"        
        
        # The method to use to check that web application is ready
        # for requests:
        #
        # The default method is 'connect' which just checks a socket
        # connection to the URI will succeed.
        #
        # The alternative method is 'recover' which will try a
        # HEAD or GET method on the URI. This can also be set to
        # 'disable' to prevent checking and redirection.
        #
        test_method = 'connect'

        # This is the control port which will be listened on for
        # command requests on. 7055 is the default if not given.
        port = '7055'
        
    """
    log = logging.getLogger('director.controllers.viewpointxulcontrol.Controller')

    def setUp(self, config):
        """
        Recovers the configuration needed to run the xulrunner and
        viewpoint application.

        :param config: This is the confiration section recovered when
        the configuration was parsed.

        :return: None
        
        """
        self.config = config

        self.pid = None
        self.commandProc = None

        self.uri = self.config.get('uri', None)           
        self.port = self.config.get('port', '7055')
        self.testMethodConfigure(config)        

        # Set up the connection to the viewpoint:
        self.dbc = viewpointdirect.DirectBrowserCalls(self.port)
        self.log.info("setUp: viewpointxulcontrol port '%s'." % self.port)
        self.log.info("setUp: URI '%s'." % self.uri)

        # Listen for the VIEWPOINT_* COMMAND events and set up the handlers.
        dispatcher.connect(
            self.setViewpointURI,
            signal = 'VIEWPOINT_SET_URI',
            sender = dispatcher.Any,
        )
        dispatcher.connect(
            self.getViewpointURI,
            signal = 'VIEWPOINT_GET_URI',
            sender = dispatcher.Any,
        )
        dispatcher.connect(
            self.replaceContent,
            signal = 'VIEWPOINT_REPLACE',
            sender = dispatcher.Any,
        )
        dispatcher.connect(
            self.viewpointQuit,
            signal = 'VIEWPOINT_QUIT',
            sender = dispatcher.Any,
        )
        self.log.info("setUp: VIEWPOINT_* signals.")
        
        
    def reply(self, messenger_event, data):
        """Called to handle the reply for a VIEWPOINT_* command event.
        """
        # The uid of the signal is used as the 'address' that
        # a reply goes back to. We'll forward the replyto which
        # the xul browser will return to us later. The method
        # dataReceived then deal with the business of sending a
        # reply.
        reply_to = messenger_event.uid
        
        self.log.debug("replyTo: dispatching reply to <%s:%s>." % (
            messenger_event, reply_to
        ))
        
        messenger.reply(messenger_event, data)
    
    
    def setViewpointURI(self, signal, sender, **kw):
        """Handle the VIEWPOINT_SET_URI command and return the reply.
        """
        self.log.debug("""setViewpointURI (VIEWPOINT_SET_URI): new_uri '%s'.""" % (kw))

        data = kw['data']
        uri = data['uri']
        
        rc = self.dbc.setBrowserUri(uri)
        self.log.debug("""setViewpointURI (VIEWPOINT_SET_URI): returned '%s' via reply.""" % (rc))

        self.reply(signal, rc)
        
        
    def getViewpointURI(self, signal, sender, **kw):
        """Handle the VIEWPOINT_GET_URI command and return the URI 
        the viewpoint is currently looking at.
        """
        self.log.debug("getViewpointURI (VIEWPOINT_GET_URI).")
        rc = self.dbc.getBrowserUri()        
        self.reply(signal, rc)

        
    def replaceContent(self, signal, sender, **kw):
        """Handle the VIEWPOINT_REPLACE command and return the reply.
        """
        self.log.debug("""replaceContent (VIEWPOINT_REPLACE): %s""" % (kw))

        data = kw['data']
        content_id = data['content_id']
        content = data['content']
       
        try:
            rc = self.dbc.replaceContent(content_id, content)
            
        except viewpointdirect.BrowserNotPresent, e:
            rc = "Replace Failed! - content_id:%s,  content:%s" % (content_id, content)
            self.log.warn("Viewpoint not present? It could also be busy: %s" % rc)
            
        self.reply(signal, rc)

        
    def viewpointQuit(self, signal, sender, **kw):
        """Handle the VIEWPOINT_QUIT command and return the reply.
        """
        self.log.warn("""replaceContent (VIEWPOINT_QUIT)""")
        self.reply(signal, 'ok')
        try:
            self.dbc.browserQuit()
        except viewpointdirect.BrowserNotPresent, e:
            self.log.warn("Viewpoint not present to shutdown.")

        
    def start(self):
        """
        This does not start a xulrunner app, its just a no-operation.

        :return: None
        
        """
    

    def isStarted(self):
        """
        Check if the viewpoint control port is present, if so then set the URI it
        should be looking at.
        
        :return: True as its not actually monitoring any started process.
        
        """
        if self.dbc.waitForReady(retries=1):
            if not self.isURICorrect(self.uri):
                # only re-check the webapp if the viewpoint isn't
                # looking at it. This reduces request load on web 
                # app.
                if self.checkForURIReadiness(self.uri):
                    self.setURI(self.uri)            
    
        return True
        

    def stop(self):
        """
        No-operation.

        :return: None
        
        """


    def isStopped(self):
        """
        No-operation.

        :return: True as no process was started to stop.
        
        """
        return True





