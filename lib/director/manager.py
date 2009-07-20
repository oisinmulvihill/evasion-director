"""

:mod:`manager` -- Main control code
=======================================

.. module:: directorX
   :platform: Unix, MacOSX, Windows
   :synopsis: Main control code for the director
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>


This module provides the Manager class which is the main director
code logic. The Manager handles the running and management of both 
the XUL Browser and the web presence.

.. autoclass:: director.manager.Manager
   :members:
   :undoc-members:

"""
import os
import sys
import time
import copy
import urllib
import random
import socket
import os.path
import logging
import StringIO
import simplejson
import subprocess

import agency
import director
import messenger
import director.config
from pydispatch import dispatcher
from director import proxydispatch
from director import viewpointdirect
from messenger import xulcontrolprotocol


def get_log():
    return logging.getLogger("director.manager")


class Manager(object):
    """Manage the running of both the XUL Browser and Web Presence services.

    """
    log = logging.getLogger("director.manager.Manager")

    def __init__(self):
        """
        """
        self.controllers = []
        

    def controllerSetup(self):
        """
        Called to load the director configuration from the raw config data.
        This will then recover and load only the relevant controller
        sections.

        After loading the controllers each one's setUp will be called, passing
        it its own local section of the configuration.

        The controllers recovered will be stored in the internal controllers
        member variable.

        :returns: None.

        """
        self.log.info("controllerSetup: loading controllers from config.")
        cfg = director.config.get_cfg().raw
        
        self.controllers = director.config.load(cfg)
        if not self.controllers:
            self.log.warn("controllerSetup: no controllers found in config.")
            
        else:
            # Setup all enabled controllers:
            for order, ctl in self.controllers:
                if ctl.disabled == 'no':
                    ctl.controller.setUp(ctl.config)


    def appmain(self, isExit):
        """I need to implement a state machine to do this properly...

        isExit:
            This is a function that will return true
            when its time to exit.

        Note: this is a thread which we are running in and the
        messenger will determine when its time to exit.
        
        """
        c = director.config.get_cfg()
        cfg = c.cfg['director']
        poll_time = float(cfg.get('poll_time'))

        # Recover the controllers from director configuration.
        self.controllerSetup()

        while not isExit():
            # Check the controllers are alive and restat if needs be:
            for order, ctl in self.controllers:

                if ctl.disabled == 'no':
                    if not ctl.controller.isStarted():
                        self.log.info("The controller '%s' needs to be (re)started." % (ctl))
                        ctl.controller.start()
                        rc = ctl.controller.isStarted()
                        self.log.info("(Re)started ok '%s'? '%s'" % (ctl, rc))            
            
            # Don't busy wait if nothing needs doing:
            time.sleep(poll_time)

        # Teardown all enabled controllers:
        for order, ctl in controllers:
            if ctl.disabled == 'no':
                ctl.controller.tearDown()


        self.log.info("appmain: Finished.")
        

    def exit(self):
        """Called by the windows service to stop the director service and
        all its children.
        
        """
        self.log.warn("exit: the director is shutting down.")
        messenger.quit()
        time.sleep(2)


    def shutdown(self):
        """Shutdown any remaining services with winKill()
        """

                
    def main(self):
        """Set up the agency layer and then start the messenger
        layer running with the app main.
        
        """
        self.log.info("main: setting up stomp connection.")        

        cfg = director.config.get_cfg().cfg
        cfg = cfg['director']
        
        # Set up the messenger protocols where using:        
        self.log.info("main: setting up stomp connection to broker.")
        messenger.stompprotocol.setup(dict(
            host=cfg.get('msg_host'),
            port=int(cfg.get('msg_port')),
            username=cfg.get('msg_username'),
            password=cfg.get('msg_password'),
            channel=cfg.get('msg_channel'),
        ))
        
        port = int(cfg.get('proxy_dispatch_port', 1901))
        self.log.info("main: setting up reply proxy dispatch http://127.0.0.1:%s/ ." % port)
        proxydispatch.setup(port)

        try:
            self.log.info("main: Running.")
            messenger.run(self.appmain)
            
        finally:
            self.log.info("main: shutdown!")
            self.shutdown()
            self.exit()
            

