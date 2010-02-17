"""
:mod:`webadminctrl`
====================

.. module:: webadminctrl
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the interface to command line processes.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This runs the webadmin without needing to spawnit under another python process.

.. autoclass:: director.controllers.webadminctrl.Controller
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

        [agency]
        # Standard options example:
        controller = 'director.controllers.webadminctrl'
        
        # (OPTIONAL) Uncomment to prevent this controller from being used.
        #disabled = 'yes'
        
        # (OPTIONAL) When to start the webadmin. It needs the broker
        # running before it will fully start up.
        order = 4
        
        # (OPTIONAL) the root of the web interface into which all other 
        # parts are plugged. This is the default but it can be easily
        # switched and overridden.
        webadmin = 'webadmin'

    """
    log = logging.getLogger('director.controllers.agencyctrl')
        
   def setUp(self, config):
        base.Controller.setUp(self, config)
        self.log.info("setUp: Not Implemented.")


    def start(self):
        self.log.info("start: Not Implemented.")


    def isStarted(self):
        self.log.info("isStarted: Not Implemented.")
        return True
    

    def stop(self):
        self.log.info("stop: Not Implemented.")
        

    def isStopped(self):
        self.log.info("isStopped: Not Implemented.")
        return True


    def tearDown(self):
        self.log.info("tearDown: Not Implemented.")
