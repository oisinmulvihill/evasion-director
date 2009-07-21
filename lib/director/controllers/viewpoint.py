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

        # Director to run the application from:
        workingdir = '.'

        # Viewpoint command line arguments to use. Currently
        # you can use:
        #
        # -startport 7055
        #    This is the control port which will be listened on for
        #    command requests on. 7055 is the default if not given.
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
    pid = None
    commandProc = None
    xulrunner = None
    args = None
    command = None
    

    def setUp(self, config):
        """
        Recovers the configuration needed to run the xulrunner and
        viewpoint application.

        :param config: This is the confiration section recovered when
        the configuration was parsed.

        :return: None
        
        """
        base.Controller.setUp(self, config)

        self.xulrunner = self.config.get('xulrunner')
        if not self.xulrunner:
            raise ValueError("No valid 'xulrunner' recovered from config!")

        self.workingdir = self.config.get('workingdir', '.')
            
        self.args = self.config.get('args', '')

        self.log.debug("setUp: xulrunner <%s> args <%s>" % (self.xulrunner, self.args))

        # Workout the viewpoint application.ini path inside the viewpoint path:
        # Fill in the template information with XUL Browser path:
        import viewpoint
        self.viewpointPath = pkg_resources.resource_filename('viewpoint','application.ini')
        self.log.info("setUp: using xulrunner '%s'." % self.xulrunner)
        self.log.info("setUp: using viewpoint from '%s'." % self.viewpointPath)
        self.log.info("setUp: using args '%s'." % self.args)
        self.command = "%s %s %s" % (self.xulrunner, self.viewpointPath, self.args)


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
        return proc.check(self.commandProc)
    

    def stop(self):
        """
        This is called to stop the viewpoint by call ints quit method and
        then telling it to quit via kill if needs be.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        if not proc.check(self.commandProc):
            self.log.info("stop: stopping the viewpoint and all its children.")
            proc.kill(self.pid)
            
        else:
            self.log.warn("stop: The no viewpoint is running please call start first!")
            

    def isStopped(self):
        """
        Check the xulrunner process is stopped by checking the control
        port and the process

        :return: True if the process has stopped otherwise False
        
        """
        return proc.check(self.commandProc)


    def tearDown(self):
        """
        
        :return: None
        
        """


