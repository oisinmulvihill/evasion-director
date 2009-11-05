"""
:mod:`manager` -- Main director control code.
==============================================

.. module:: directorX
   :platform: Unix, MacOSX, Windows
   :synopsis: Main director control code.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: director.manager.Manager
   :members:
   :undoc-members:

"""
import time
import logging

import agency
import director
import messenger
import director.config
from pydispatch import dispatcher
from director import proxydispatch
from director import viewpointdirect
from messenger import xulcontrolprotocol

try:
	import decorator # help for bbfreeze.
except ImportError, e:
	pass


def get_log():
    return logging.getLogger("director.manager")


class Manager(object):
    """Manages the running services determined by the configuration
    that was loaded.

    The manager expects to find a [director] section in the configuration::

        [director]
        # The broker connection details. Required if nobroker = 'no' (default):
        msg_host = "127.0.0.1"
        msg_port = 61613
        msg_username = ''
        msg_password = ''
        msg_channel = 'evasion'

        # (OPTIONAL): Set this to 'yes' if you wish to stop the director connecting to the broker.
        disable_broker = 'no'

        # (OPTIONAL) Prevent director busy waiting. This just limits the time between maintenances checks.
        # This is in seconds or fractions of seconds, the default being 0.1s.
        poll_time = 0.1

        # (OPTIONAL): To disable the special proxy dispatch set this to 'yes'
        noproxydispatch = 'no'

        # (OPTIONAL): Web app local reply dispatch XML-RPC service i.e. http://localhost:<this port>/RPC2.
        proxy_dispatch_port = 1901

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
        if self.controllers:
            # Setup all enabled controllers:
            for order, ctl in self.controllers:
                if ctl.disabled == 'no':
                    ctl.controller.setUp(ctl.config)
        else:
            self.log.warn("controllerSetup: no controllers found in config.")


    def appmain(self, isExit):
        """
        Run the main program loop.

        :param isExit: This is a function that will return true
        when its time to exit.

        Note: this is a thread which we are running in and the
        messenger will determine when its time to exit.
        
        """
        c = director.config.get_cfg()
        cfg = c.cfg['director']
        poll_time = float(cfg.get('poll_time', '1'))

        # Register messenger hook for shutdown()
        def signal_exit(signal, sender, **data) :
            self.log.warn("main: EVT_EXIT_ALL received, exiting...")
            self.exit()
            
        dispatcher.connect(
          signal_exit,
          signal=messenger.EVT("EVT_EXIT_ALL")
        )        
        self.log.info("main: EVT_EXIT_ALL signal setup.")

        # Recover the controllers from director configuration.
        self.controllerSetup()

        while not isExit():
            # Check the controllers are alive and restat if needs be:
            for order, ctl in self.controllers:            
                if ctl.disabled == 'no':
                    if not ctl.controller.isStarted():
                        self.log.info("The controller '%s' needs to be started." % (ctl))
                        ctl.controller.start()
                        rc = ctl.controller.isStarted()
                        self.log.info("Started ok '%s'? '%s'" % (ctl.name, rc))            
            
            # Don't busy wait if nothing needs doing:
            time.sleep(poll_time)

        self.log.info("appmain: Finished.")
        

    def exit(self):
        """
        Called after shutdown() to tell twisted to exit causing the program
        to quit normally.
        """
        self.log.warn("exit: the director is shutting down.")
        messenger.quit()
        time.sleep(2)


    def shutdown(self):
        """
        Shutdown any remaining services and call their tearDown methods.

        This is called before exit() is called.
        
        """
        # Stop all enabled controllers:
        for order, ctl in self.controllers:
            ctl.controller.stop()

        # Teardown all enabled controllers:
        for order, ctl in self.controllers:
            ctl.controller.tearDown()

                
    def main(self):
        """
        The main thread in which twisted and the messagin system runs. The
        manager main run inside its own thread. The appman(...) is the
        main of the director.
        
        """
        self.log.info("main: setting up stomp connection.")        

        cfg = director.config.get_cfg().cfg
        cfg = cfg['director']
        
        disable_broker = cfg.get('disable_broker', 'no')
        if disable_broker == 'no':
            # Set up the messenger protocols where using:
            self.log.info("main: setting up stomp connection to broker.")
            messenger.stompprotocol.setup(dict(
                host=cfg.get('msg_host'),
                port=int(cfg.get('msg_port')),
                username=cfg.get('msg_username'),
                password=cfg.get('msg_password'),
                channel=cfg.get('msg_channel'),
            ))
        else:
            self.log.warn("main: the director's broker connection is disabled (disable_broker = 'yes').")
            
        noproxydispatchbroker = cfg.get('noproxydispatch', 'no')
        if noproxydispatchbroker == 'no':
            port = int(cfg.get('proxydispatch_port', 1901))
            self.log.info("main: setting up reply proxy dispatch http://127.0.0.1:%s/ ." % port)
            proxydispatch.setup(port)
        else:
            self.log.warn("main: the director's proxydispatch is disabled (noproxydispatch = 'yes').")

        try:
            self.log.info("main: Running.")
            messenger.run(self.appmain)
            
        finally:
            self.log.info("main: shutdown!")
            self.shutdown()
            self.exit()
            

