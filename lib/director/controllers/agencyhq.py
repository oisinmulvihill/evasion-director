"""
:mod:`agencyhq` -- This runs the agency without needing to spawnit under another python process.
=================================================================================================

.. module:: agencyhq
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the interface to command line processes.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This runs the agency without needing to spawnit under another python process.

.. autoclass:: director.controllers.agencyhq.Controller
   :members:
   :undoc-members:

"""
import os
import logging
import subprocess

import agency
import director
from agency.manager import Manager
from director.controllers import base


class Controller(base.Controller):
    """
    This controller typically has the following configuration::

        [agencyhq]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = 'director.controllers.agencyhq'

    The agency uses the raw director config to look for
    agents to load and run. It will recover the configuration
    using director.config.get_cfg().raw

    """
    log = logging.getLogger('director.controllers.commandline')
        
        
    def setUp(self, config):
        """
        This looks in the configuration and recovers the command and
        workingdir values. These will be used later when start() is
        called.
        
        No process is started at this point.

        :param config: This is the confiration section recovered when
        the configuration was parsed.

        :return: None
        
        """
        base.Controller.setUp(self, config)

        self.isRunning = False

        # Get the raw config and recover the agents we'll be using:
        self.log.debug("setUp: setting up the agency and recovering agents.")
        self.manager = Manager()
        cfg = director.config.get_cfg().raw
        self.manager.load(cfg)
        self.manager.setUp()        



    def start(self):
        """
        This starts a new process based on the command line and
        working directory configured by the end user.

        If start is called after the first call, it will be
        ignored and a warning to that effect will be logged.
        
        :return: None
        
        """
        self.manager.start()
        self.isRunning = True


    def isStarted(self):
        """
        This is called to wait for the process to finish loading and report
        is ready.

        This method is called directly after a call to the start method and
        it is acceptable to block waiting.

        :return: True if the process is running otherwise False
        
        """
        return self.isRunning
    

    def stop(self):
        """
        This is called to stop the process that was set up in an earlier
        call to the setup(...) method.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        self.manager.stop()
        self.isRunning = False
        

    def isStopped(self):
        """
        This is called to wait for the process to finish stopping.

        This method is called directly after a call to the stop method and
        it is acceptable to block waiting.

        :return: True if the process has stopped otherwise False
        
        """
        return self.isRunning


    def tearDown(self):
        """
        Close the agency down, shot all the agents in the head. The
        calls the agency manager shutdown which
        
        :return: None
        
        """
        self.manager.shutdown()
