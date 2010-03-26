"""
:mod:`viewpointpassive` -- This doesn't start a viewpoint but controls one if runnning.
=========================================================================================

.. module:: evasion.director.controllers.viewpointpassive
   :platform: Unix, MacOSX, Windows
   :synopsis: This doesn't start a viewpoint but controls one if runnning.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: evasion.director.controllers.viewpointpassive.Controller
   :members:
   :undoc-members:

"""
import os
import socket
import logging
import subprocess
import pkg_resources

import simplejson

from evasion import agency
from evasion import director
from evasion.director.tools import net
from evasion.director import viewpointdirect
from evasion.director.controllers import viewpoint


class Controller(viewpoint.Controller):
    """
    This controller typically has the following configuration::

        [viewpoint]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = 'evasion.director.controllers.viewpointpassive'

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
        # HEAD or GET method on the URI.
        #
        test_method = 'connect'

        # This is the control port which will be listened on for
        # command requests on. 7055 is the default if not given.
        port = '7055'
        
    """
    log = logging.getLogger('evasion.director.controllers.viewpointctrl.Controller')

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

        self.dbc = viewpointdirect.DirectBrowserCalls(self.port)
        self.log.info("setUp: viewpoint port '%s'." % self.port)
        self.log.info("setUp: URI '%s'." % self.uri)


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
        This is called to stop the viewpoint by call ints quit method and
        then telling it to quit via kill if needs be.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """


    def isStopped(self):
        """
        No-operation.

        :return: True as no process was started to stop.
        
        """
        return True


    def tearDown(self):
        """
        :return: None
        """


