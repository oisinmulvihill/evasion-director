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
import logging
import subprocess
import pkg_resources

import agency
import director
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

        # This is the control port which will be listened on for
        # command requests on. 7055 is the default if not given.
        port = '7055'
        
        # Director to run the application from:
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


    def isStarted(self):
        """
        Check the xulrunner process is running and then attempt to connect
        to its control port.
        
        :return: True if the process is running otherwise False
        
        """
        rc = self.dbc.waitForReady(retries=10)
        return rc
    

    def stop(self):
        """
        This is called to stop the viewpoint by call ints quit method and
        then telling it to quit via kill if needs be.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        if self.pid:
            # Ask the viewpoint nicely to shutdown:
            self.log.info("stop: asking viewpoint to shutdown.")
            rc = self.dbc.browserQuit()

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
            rc = self.dbc.waitForReady(retries=1)

        return rc


    def tearDown(self):
        """
        
        :return: None
        
        """


