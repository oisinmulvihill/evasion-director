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

import director
from director.tools import proc
from director.controllers import base


class Controller(base.Controller):
    """
    This controller typically has the following configuration::

        [agencyhq]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = 'director.controllers.agencyhq'

        # Command Line specific options:
        command = 'mycommand -someoption -anotheroption=abc'
        workingdir = '/tmp'

    The command is the shell based command you would call if
    you were running the command out side of the director.

    The workingdir is the place on the file system in which
    the process wil be run. You could place files your command
    needs there and it will find them in the current path.

    """
    log = logging.getLogger('director.controllers.commandline')

    pid = None
    commandProc = None


    def check(self):
        """
        Called to check if the process is currently running.

        :returns: True for process is running otherwise False.
        
        """
        returned = False

        if self.commandProc and self.commandProc.poll() is None:
            returned = True

        return returned
        
        
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

        self.command = self.config.get('command')
        if not self.command:
            raise ValueError("No valid command recovered from config!")
            
        self.workingdir = self.config.get('workingdir')
        if not self.command:
            raise ValueError("No valid workingdir recovered from config!")
        
        if not os.path.isdir(self.workingdir):
            raise ValueError("The directory to run from '%s' does not exist!" % self.workingdir)

        self.log.debug("setUp: command <%s> workingdir <%s>" % (self.command, self.workingdir))


    def start(self):
        """
        This starts a new process based on the command line and
        working directory configured by the end user.

        If start is called after the first call, it will be
        ignored and a warning to that effect will be logged.
        
        :return: None
        
        """
        if not self.check():
            self.commandProc = subprocess.Popen(
                args = self.command,
                shell=True,
                cwd=self.workingdir,
                )
            self.pid = self.commandProc.pid

        else:
            self.log.warn("start: The process '%s' is running, please call stop first!" % self.pid)


    def isStarted(self):
        """
        This is called to wait for the process to finish loading and report
        is ready.

        This method is called directly after a call to the start method and
        it is acceptable to block waiting.

        :return: True if the process is running otherwise False
        
        """
        return self.check()
    

    def stop(self):
        """
        This is called to stop the process that was set up in an earlier
        call to the setup(...) method.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        if not self.check():
            self.log.info("stop: stopping the process and all its children.")
            proc.kill(self.pid)
            
        else:
            self.log.warn("stop: The no process is running please call start first!")
            

    def isStopped(self):
        """
        This is called to wait for the process to finish stopping.

        This method is called directly after a call to the stop method and
        it is acceptable to block waiting.

        :return: True if the process has stopped otherwise False
        
        """
        return self.check()


    def tearDown(self):
        """
        
        :return: None
        
        """
