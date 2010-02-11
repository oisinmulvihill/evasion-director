"""
:mod:`signals` -- Signals handled by the director
=================================================

.. module:: director.signals
   :platform: Unix, MacOSX, Windows
   :synopsis: Main director control code.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: director.signals.SignalTimeout
   :members:
   :undoc-members:
   
.. autoclass:: director.signals.SignalsReceiver
   :members:
   :undoc-members:

.. autoclass:: director.signals.SignalsSender
   :members:
   :undoc-members:

"""
import uuid
import pprint
import logging

from pydispatch import dispatcher

import messenger
import director.config


class SignalTimeout(Exception):
    """
    Raise by the SignalsSender when no reponse has been
    receieved to a signal within a certain period of time.
    """


class SignalsSender(object):
    """
    This class implements the API others can use to talk
    to the director via signals. This API hides the lower
    level details of sending and waiting for replies from 
    the end user.
    
    """
    def __init__(self):
        self.log = logging.getLogger('director.signals.SignalsSender')


    def ping(self, timeout=10, testing=None):
        """
        Called to check if the director is actually there and
        responding, otherwise we could be waiting forever for
        nothing to happen.

        :param timeout: This is the amount of time (in seconds) 
        used to wait for the director to respond. If a response 
        isn't received within this then SignalTimeout will be 
        raised.

        Event Dispatched: EVT_DIRECTOR_PING

        """
        token = str(uuid.uuid4())
        self.log.debug("ping: waiting for director with token '%s'." % (token))
        evt = messenger.EVT("EVT_DIRECTOR_PING")
        if testing:
            # use the unittest's EVT_DIRECTOR_PING instead.
            evt = testing            
        try:
            rc = messenger.send_await(evt, token, timeout=timeout)
            rtoken = rc['data']
            if token != rtoken:
                self.log.warn("ping: received ping token '%s' is different to '%s'" % (token, rtoken))
            else:
                self.log.debug("ping: received correct ping from director." % ())

        except messenger.EventTimeout, e:
            raise SignalTimeout("Director presence check failed! Is it running?")        


    def webadminModules(self):
        """
        Called to ask the director for a list of python modules
        which will form the basis of the webadmin frontend.

        Event Dispatched: EVT_WEBADMIN_MODULES

        """
        modules = []
        self.log.debug("webadminModules: asking the director for webadmin modules.")
        evt = messenger.EVT("EVT_WEBADMIN_MODULES")
        try:
            rc = messenger.send_await(evt)
            modules = rc['data']
            self.log.debug("ping: received correct ping from director." % ())

        except messenger.EventTimeout, e:
            raise SignalTimeout("Timeout! No response to webadmin module request.")        
        
        return modules



class SignalsReceiver(object):
    """
    This class is used by the director's Manager to implement
    behaviour in reponse to signals/events we receive locally
    or remotely over the message bus.
    
    """
    def __init__(self, manager):
        """
        :parma manager: this is an instance of the 
        director.manager.Manager class, signal handlers
        can use.
        
        """
        self.log = logging.getLogger('director.signals.SignalsReceiver')
        self.manager = manager


    def signalPing(self, signal, sender, **data):
        """
        Called to handle the EVT_DIRECTOR_PING signal, which is
        used by other to see if the director is present and 
        responding to signals.
        
        :param data['data]: should contain some string the callee
        wished to receive back. If the SignalsSender.ping() was
        called then this will be a uuid string. The ping function
        will warn if the same uuid is not returned.
        
        """
        rtoken = data['data']
        self.log.debug("main: EVT_DIRECTOR_PING received token '%s' replying with same." % (rtoken))
        messenger.reply(signal, rtoken)


    def signalExit(self, signal, sender, **data):
        """
        Called to handle the EVT_EXIT_ALL signal, which tells
        the director to shutdown normally.
        
        """
        self.log.warn("main: EVT_EXIT_ALL received, exiting...")
        self.manager.exit()


    def signalWebAdminModules(self, signal, sender, **data):
        """
        Called to handle the signal EVT_WEBADMIN_MODULES
        """
        self.log.info("main: EVT_WEBADMIN_MODULES received.")
        
        returned = director.config.webadmin_modules(self.manager.controllers)

        self.log.debug("main: EVT_WEBADMIN_MODULES returned '%s'." % pprint.pformat(
            returned
        ))
        
        messenger.reply(signal, returned)


    def setup(self):
        """
        Called to set up the signal handlers which subscribe to all the 
        events this class currently supports.
        
        """
        # Register a quick event to check if the director is present
        # and responding on the message bus.
        dispatcher.connect(
            self.signalPing,
            signal=messenger.EVT("EVT_DIRECTOR_PING")
        )        
        
        self.log.info("signalSetup: EVT_EXIT_ALL signal setup.")
        # Register messenger hook for shutdown()
        dispatcher.connect(
            self.signalExit,
            signal=messenger.EVT("EVT_EXIT_ALL")
        )        
        self.log.info("signalSetup: EVT_EXIT_ALL signal setup.")
            
        # Register messenger hook for webadmin module list:
        dispatcher.connect(
            self.signalWebAdminModules,
            signal=messenger.EVT("EVT_WEBADMIN_MODULES")
        )        
        self.log.info("signalSetup: EVT_WEBADMIN_MODULES signal setup.")
