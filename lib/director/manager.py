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
import sys
import time
import logging
import traceback

import agency
import director
import messenger
import director.config
from director import signals
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

    The manager expects to find a [director] section in the configuration.
    For more on this see director.configobjs.Director doc string.

    """
    log = logging.getLogger("director.manager.Manager")

    def __init__(self):
        """
        """
        self.controllers = []
        self.signals = signals.SignalsReceiver(self)
        

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
        c = director.config.get_cfg()
        
        # Recover and import the controllers:
        self.controllers = director.config.load_controllers(c.cfg)
        self.log.info("controllerSetup: %s controller(s) recovered." % len(self.controllers))
        
        if self.controllers:
            # Setup all enabled controllers:
            for ctl in self.controllers:
                controller = ctl.mod
                if not controller:
                    # skip
                    continue
                try:
                    if ctl.disabled == 'no':
                        controller.setUp(ctl.config)
                except:
                    self.log.exception("%s setUp error: " % ctl)
                    sys.stderr.write("%s setUp error: %s" % (ctl, self.formatError()))
        else:
            self.log.warn("controllerSetup: no controllers found in config.")


    def shutdown(self):
        """
        Shutdown any remaining services and call their tearDown methods.

        This is called before exit() is called.
        
        """
        # Stop all enabled controllers:
        for ctl in self.controllers:
            controller = ctl.mod
            if not controller:
                # skip
                continue
            try:
                controller.stop()
            except:
                self.log.exception("%s stop error: " % ctl)
                sys.stderr.write("%s stop error: %s" % (ctl, self.formatError()))

        # Teardown all enabled controllers:
        for ctl in self.controllers:
            controller = ctl.mod
            if not controller:
                # skip
                continue
            try:
                controller.tearDown()
            except:
                self.log.exception("%s tearDown error: " % ctl)
                sys.stderr.write("%s tearDown error: %s" % (ctl, self.formatError()))


    def appmain(self, isExit):
        """
        Run the main program loop.

        :param isExit: This is a function that will return true
        when its time to exit.

        Note: this is a thread which we are running in and the
        messenger will determine when its time to exit.
        
        """
        c = director.config.get_cfg()
        poll_time = float(c.director.poll_time)
            
        # Set up all signals handlers provided by the director:
        self.signals.setup()

        # Recover the controllers from director configuration.
        self.controllerSetup()

        while not isExit():
            # Check the controllers are alive and restat if needs be:
            for ctl in self.controllers:            
                if ctl.disabled == 'no' and ctl.mod:
                    try:
                        if not ctl.mod.isStarted():
                            self.log.info("appmain: The controller '%s' needs to be started." % (ctl))
                            ctl.mod.start()
                            rc = ctl.mod.isStarted()
                            self.log.info("appmain: Started ok '%s'? '%s'" % (ctl.name, rc))            
                    except:
                        self.log.exception("%s appmain error: " % ctl)
                        sys.stderr.write("%s appmain error: %s" % (ctl, self.formatError()))

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
    
    
    def formatError(self):
        """Return a string representing the last traceback.
        """
        exception, instance, tb = traceback.sys.exc_info()
        error = "".join(traceback.format_tb(tb))      
        return error


    def main(self):
        """
        The main thread in which twisted and the messagin system runs. The
        manager main run inside its own thread. The appman(...) is the
        main of the director.
        
        """
        self.log.info("main: setting up stomp connection.")        
        c = director.config.get_cfg()
        
        disable_broker = c.director.disable_broker
        if disable_broker == 'no':
            # Set up the messenger protocols where using:
            self.log.info("main: setting up stomp connection to broker.")
            
            messenger.stompprotocol.setup(dict(
                    host=c.director.msg_host,
                    port=int(c.director.msg_port),
                    username=c.director.msg_username,
                    password=c.director.msg_password,
                    channel=c.director.msg_channel,
            ))
            
        else:
            self.log.warn("main: the director's broker connection is disabled (disable_broker = 'yes').")

        noproxydispatchbroker = c.director.noproxydispatch
        if noproxydispatchbroker == 'no':
            port = int(c.director.proxy_dispatch_port)
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


            

