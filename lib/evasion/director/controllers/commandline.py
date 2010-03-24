"""
:mod:`commandline` -- This provides the interface to command line processes.
=============================================================================

.. module:: evasion.director.controllers.commandline
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the interface to command line processes.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This provides the interface to command line processes.

.. autoclass:: evasion.director.controllers.commandline.Controller
   :members:
   :undoc-members:

"""
import os
import logging
import subprocess

from evasion.director.tools import proc
from evasion.director.controllers import base


class Controller(base.Controller):
    """
    This is the command line controller that implements the
    launching of processes via pythons subprocess module.

    This controller typically adds two extra options to the
    standard controller configuration::

        [my_proc_name]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = ...

        # Command Line specific options:
        command = 'mycommand -someoption -anotheroption=abc'
        workingdir = '/tmp'

    The command is the shell based command you would call if
    you were running the command out side of the director.

    The workingdir is the place on the file system in which
    the process wil be run. You could place files your command
    needs there and it will find them in the current path.

    """
    log = logging.getLogger('evasion.director.controllers.commandline')    

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

        self.pid = None
        self.commandProc = None

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
        if not proc.check(self.commandProc):
            self.commandProc = subprocess.Popen(
                args = self.command,
                shell=True,
                cwd=self.workingdir,
                )
            
            self.pid = self.commandProc.pid
            self.log.info("start:  '%s' running. PID %s" % (self.command, self.pid))

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
        return proc.check(self.commandProc)
    

    def stop(self):
        """
        This is called to stop the process that was set up in an earlier
        call to the setup(...) method.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        if self.pid:
            self.log.info("stop: stopping the process PID:'%s' and all its children." % self.pid)
            proc.kill(self.pid)
        else:
            self.log.warn("stop: process not running to stop it.")
            

    def isStopped(self):
        """
        This is called to wait for the process to finish stopping.

        This method is called directly after a call to the stop method and
        it is acceptable to block waiting.

        :return: True if the process has stopped otherwise False
        
        """
        return proc.check(self.commandProc)


    def tearDown(self):
        """
        
        :return: None
        
        """

