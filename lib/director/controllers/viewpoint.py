"""
:mod:`viewpointctrl` -- This is the director compatible controller for the viewpoint.
======================================================================================

.. module:: viewpointctrl
   :platform: Unix, MacOSX, Windows
   :synopsis: This is the director compatible controller for the viewpoint.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: director.controllers.viewpointctrl.Controller
   :members:
   :undoc-members:

"""
import os
import socket
import logging
import subprocess
import pkg_resources

import simplejson

import agency
import director
from director.tools import net
from director.tools import proc
from agency.manager import Manager
from director import viewpointdirect
from director.controllers import base


class Controller(base.Controller):
    """
    This controller typically has the following configuration::

        [viewpoint]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = 'director.controllers.viewpoint'

        # Specific configuration:
        #
        # The xulrunner exe to use (command and/or path to exe):
        xulrunner = 'xulrunner'

        # The URI to connect to when the URI is present and the viewpoint
        # is ready to recieve requests. The viewpoint will also be kept
        # looking at this URI so it can't navigate away out of the app.
        uri = "http://myhost:myport/myapp"        

        # This is the control port which will be listened on for
        # command requests on. 7055 is the default if not given.
        port = '7055'
        
        # Director to run the xul application from:
        workingdir = '.'

        # Viewpoint command line arguments to use. Currently
        # you can use:
        #
        # -starturi chrome://viewpoint/content/static/startup.html
        #    The URI to display on start up. By default it uses
        #    its internal evasion viewpoint page.
        #
        # -nofullscreen no | yes
        #    Disable the full screen mode. The default is to run
        #    in full screen mode.
        #
        # -development no | yes
        #    Show an address bar and a reload button to aid in
        #    development of an application.
        #
        args = ''

    """
    log = logging.getLogger('director.controllers.viewpointctrl.Controller')

    def setUp(self, config):
        """
        Recovers the configuration needed to run the xulrunner and
        viewpoint application.

        :param config: This is the confiration section recovered when
        the configuration was parsed.

        :return: None
        
        """
        base.Controller.setUp(self, config)

        self.pid = None
        self.commandProc = None

        self.xulrunner = self.config.get('xulrunner')
        if not self.xulrunner:
            raise ValueError("No valid 'xulrunner' recovered from config!")

        self.uri = self.config.get('uri', None)

        self.workingdir = self.config.get('workingdir', '.')
            
        self.port = self.config.get('port', '7055')

        self.dbc = viewpointdirect.DirectBrowserCalls(self.port)
        
        self.args = self.config.get('args', '')

        self.log.debug("setUp: xulrunner <%s> args <%s>" % (self.xulrunner, self.args))

        # Workout the viewpoint application.ini path inside the viewpoint path:
        # Fill in the template information with XUL Browser path:
        import viewpoint
        self.viewpointPath = pkg_resources.resource_filename('viewpoint','application.ini')
        self.log.info("setUp: using xulrunner '%s'." % self.xulrunner)
        self.log.info("setUp: using viewpoint from '%s'." % self.viewpointPath)
        self.log.info("setUp: viewpoint port '%s'." % self.port)
        self.log.info("setUp: URI '%s'." % self.uri)
        self.log.info("setUp: using args '%s'." % self.args)
        self.command = "%s %s -startport %s %s" % (self.xulrunner, self.viewpointPath, self.port, self.args)


    def start(self):
        """
        This starts the viewpoint app.

        If start is called after the first call, it will be
        ignored and a warning to that effect will be logged.
        
        :return: None
        
        """
        if not proc.check(self.commandProc):
            self.log.debug("start: command '%s'." % self.command)            
            self.commandProc = subprocess.Popen(
                args = self.command,
                shell=True,
                cwd=self.workingdir,
                )
            self.pid = self.commandProc.pid

        else:
            self.log.warn("start: The viewpoint '%s' is running, please call stop first!" % self.pid)


    def checkForURIReadiness(self, uri):
        """
        Called to see if the given uri is available for the viewpoint 
        to load.
        
        If the URI is present I.E. we go a get and get 200 back
        then it is considered as available.
        
        :param uri: this is the resource to check if its available. 

        :returns: True if the URI is responding to get requests,
        otherwise False.
        
        """
        return net.wait_for_ready(uri, retries=1)

    
    def isURICorrect(self, uri):
        """
        """
        returned = False
        
        try:
            data = self.dbc.getBrowserUri()
        except viewpointdirect.BrowserNotPresent, e:
            self.log.error("isURICorrect: %s" % str(e))            
        else:
            if data:
                rc = simplejson.loads(data)
                vp_uri = rc['data']
                if vp_uri.startswith(uri):
                    returned = True
                else:
                    self.log.info("isURICorrect: current URI:'%s', correct URI:'%s'." % (vp_uri, uri))            
                
        return returned
        

    def setURI(self, uri):
        """
        Called to set the URI the viewpoint should be looking at.
        
        This also checks that the app hasn't browsed away from the
        application and repoints it back at the original URI. If
        the browser URI doesn't start with the URI mentioned in the
        config then the repointing is done.
        
        """
        if not self.isURICorrect(uri):
            # Were not looking at app. Repointing...
            try:
                self.dbc.setBrowserUri(uri) 
            except viewpointdirect.BrowserNotPresent, e:
                self.log.error("setURI: %s" % str(e))            


    def isStarted(self):
        """
        Check the xulrunner process is running and then attempt to connect
        to its control port.
        
        :return: True if the process is running otherwise False
        
        """
        rc = proc.check(self.commandProc)
        if rc:
            if self.dbc.waitForReady(retries=1):
                if self.checkForURIReadiness(self.uri):
                    self.setURI(self.uri)            
    
        return rc
        

    def stop(self):
        """
        This is called to stop the viewpoint by call ints quit method and
        then telling it to quit via kill if needs be.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        rc = proc.check(self.commandProc)
        if rc:
            # Ask the viewpoint nicely to shutdown:
            self.log.info("stop: asking viewpoint to shutdown.")
            try:
                rc = self.dbc.browserQuit()
            except viewpointdirect.BrowserNotPresent, e:
                pass

            self.log.info("stop: stopping the viewpoint PID:'%s' and all its children." % self.pid)
            proc.kill(self.pid)
        else:
            self.log.warn("stop: viewpoint not running to stop it.")

            

    def isStopped(self):
        """
        Check the xulrunner process is stopped by checking the control
        port and the process

        :return: True if the process has stopped otherwise False
        
        """
        rc = proc.check(self.commandProc)
        if rc:
            # Check if the comms port is closed:
            rc = self.dbc.waitForReady(retries=5)

        return rc


    def tearDown(self):
        """
        
        :return: None
        
        """


