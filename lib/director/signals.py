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
import traceback

from pydispatch import dispatcher

import messenger
import director.config

# Default time in seconds before raising timeout:
DEFAULT_TIMEOUT = 60


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
        sig = messenger.EVT("EVT_DIRECTOR_PING")
        if testing:
            # use the unittest's EVT_DIRECTOR_PING instead.
            sig = testing            
        try:
            rc = messenger.send_await(sig, token, timeout=timeout)
            rtoken = rc['data']['data']
            if token != rtoken:
                self.log.warn("ping: received ping token '%s' is different to '%s'" % (token, rtoken))
            else:
                self.log.debug("ping: received correct ping from director." % ())

        except messenger.EventTimeout, e:
            raise SignalTimeout("Director presence check failed! Is it running?")        


    def controllerState(self, timeout=DEFAULT_TIMEOUT):
        """
        Called to return the state of all controllers listed in
        the configuration. 

        :param timeout: This is the amount of time (in seconds) 
        used to wait for the director to respond. If a response 
        isn't received within this then SignalTimeout will be 
        raised.
        
        :returns: See SignalReceiver controllerState.

        Event Dispatched: EVT_DIRECTOR_CTRLSTATE

        """
        sig = messenger.EVT("EVT_DIRECTOR_CTRLSTATE")
        try:
            self.log.debug("controllerState: (request sig id %s) getting controller state." % sig.uid)
            rc = messenger.send_await(sig)

        except messenger.EventTimeout, e:
            self.log.error("controllerState: (request sig id %s) event timeout!" % sig.uid)
            raise SignalTimeout("Director communication timeout (%s)s! Is it running?" % timeout)

        else:
            self.log.debug("controllerState: (reply for sig id %s) recovered controller state ok." % sig.uid)
            rc = rc['data']
        
        return rc    


    def controllerStart(self, name, timeout=DEFAULT_TIMEOUT):
        """
        Called to tell a controller to start running. 

        :param name: This will contain the name of the controller 
        to be started. This name is the same name as that in the 
        configuration section.
        
        :param timeout: This is the amount of time (in seconds) 
        used to wait for the director to respond. If a response 
        isn't received within this then SignalTimeout will be 
        raised.
        
        :returns: See SignalReceiver controllerStart.

        Event Dispatched: EVT_DIRECTOR_CTRLSTART

        """
        sig = messenger.EVT("EVT_DIRECTOR_CTRLSTART")
        try:
            self.log.debug("controllerStart: (request sig id %s) getting controller state." % sig.uid)
            rc = messenger.send_await(sig, name)

        except messenger.EventTimeout, e:
            self.log.error("controllerStart: (request sig id %s) event timeout!" % sig.uid)
            raise SignalTimeout("Director communication timeout (%s)s! Is it running?" % timeout)

        else:
            self.log.debug("controllerStart: (reply for sig id %s) recovered controller state ok." % sig.uid)
            rc = rc['data']
        
        return rc    


    def controllerStop(self, name, timeout=DEFAULT_TIMEOUT):
        """
        Called to tell a controller to stop running. 

        :param name: This will contain the name of the controller 
        to be started. This name is the same name as that in the 
        configuration section.
        
        :param timeout: This is the amount of time (in seconds) 
        used to wait for the director to respond. If a response 
        isn't received within this then SignalTimeout will be 
        raised.
        
        :returns: See SignalReceiver controllerStart.

        Event Dispatched: EVT_DIRECTOR_CTRLSTOP

        """
        sig = messenger.EVT("EVT_DIRECTOR_CTRLSTOP")
        try:
            self.log.debug("controllerStop: (request sig id %s) getting controller state." % sig.uid)
            rc = messenger.send_await(sig, name)

        except messenger.EventTimeout, e:
            self.log.error("controllerStop: (request sig id %s) event timeout!" % sig.uid)
            raise SignalTimeout("Director communication timeout (%s)s! Is it running?" % timeout)

        else:
            self.log.debug("controllerStop: (reply for sig id %s) recovered controller state ok." % sig.uid)
            rc = rc['data']
        
        return rc    


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


    def resultDict(self, data, result='ok'):
        """
        Return an empty signal response which will be filled out
        
        :param result: 'ok' or 'error'
        :param data: any given data type that can be pickled.
        
        :returns: dict(result=result, data=data)
        
        """
        result = result.lower()
        
        if result not in ['ok','error']:
            raise ValueError("Incorrect result value '%s'." % result)
            
        return dict(result=result, data=data)


    def formatError(self):
        """Return a string representing the last traceback.
        """
        exception, instance, tb = traceback.sys.exc_info()
        error = "".join(traceback.format_tb(tb))      
        return error


    def signalPing(self, signal, sender, **data):
        """
        Called to handle the EVT_DIRECTOR_PING signal, which is
        used by other to see if the director is present and 
        responding to signals.
        
        :param data['data]: should contain some string the callee
        wished to receive back. If the SignalsSender.ping() was
        called then this will be a uuid string. The ping function
        will warn if the same uuid is not returned.
        
        :returns: a call result dict.
            
            rc['result'] = 'ok'
            
            rc['data'] = the token we were given.
            
        """
        rtoken = data['data']
        self.log.debug("main: EVT_DIRECTOR_PING received token '%s' replying with same." % (rtoken))
        messenger.reply(signal, self.resultDict(rtoken))


    def signalControllerState(self, signal, sender, **data):
        """
        Called to handle the EVT_DIRECTOR_CTRLSTATE signal, which 
        is used to return the state of all controllers listed in
        the configuration. 
        
        :param: None
        
        :returns: a call result dict.
            
            rc['result'] = 'ok' | 'error'
        
            For ok result:
            
            rc['data'] = [
                dict(name='..name..', disabled='no'|'yes', started=False | True, config={...}),
                :
                etc
            ]
            
            For error result:
            
            rc['data'] = 'Error / Exception message'

        Note: this will contain every controller except the 
        director controller.
            
        Event Dispatched: EVT_DIRECTOR_CTRLSTATE

        """
        controller_state = []
        try:
            self.log.debug("controllerState: received request (sig id %s)." % signal.uid)
            
            c = director.config.get_cfg()
            
            for ctrl in c.cfg:
                if ctrl.name == 'director':
                    # skip the director as its not a normal controller.
                    continue
                
                # Recover the config for just this controller:
                ctrl_config = {}
                if ctrl.config:
                    ctrl_config = ctrl.config
                
                # Check if the controller module is present and actually running.
                started = False
                if ctrl.mod:
                    started = ctrl.mod.isStarted()
            
                controller_state.append(dict(
                    name=ctrl.name,
                    disabled=ctrl.disabled,
                    started=started,
                    config=ctrl_config,
                ))
            
        except:
            self.log.exception("controllerState: error handling signal (sig id %s) - " % signal.uid)
            msg = self.formatError()
            rc = self.resultDict(msg, 'error')

        else:
            rc = self.resultDict(controller_state)

        self.log.debug("controllerState: replying to request (sig id %s) - " % signal.uid)
        messenger.reply(signal, rc)


    def signalControllerStart(self, signal, sender, **data):
        """
        Called to handle the EVT_DIRECTOR_CTRLSTART signal, which 
        is used to return the result of a start command. 
        
        :param data['data]: This will contain the name of the
        controller to be started. This name is the same name
        as that in the configuration section.
        
        :returns: a call result dict.
            
            rc['result'] = 'ok' | 'error'
        
            For ok result:
            
            rc['data'] = ''
            
            For error result:
            
            rc['data'] = 'Error / Exception message'

        Note: this will contain every controller except the 
        director controller.
            
        Event Dispatched: EVT_DIRECTOR_CTRLSTART

        """
        name = data['data']
        msg = ''
        try:
            self.log.debug("signalControllerStart: received request (sig id %s)." % signal.uid)
            
            c = director.config.get_cfg()
            for ctrl in c.cfg:
                if ctrl.name == name:
                    if ctrl.disabled == "yes":
                        msg = "The controller '%s' is disabled and cannot be started" % name
                    else:
                        ctrl.mod.start()
                        msg = ctrl.mod.isStarted()
                        
                    break

        except:
            self.log.exception("signalControllerStart: error handling signal (sig id %s) - " % signal.uid)
            msg = self.formatError()
            rc = self.resultDict(msg, 'error')

        else:
            rc = self.resultDict(msg)

        self.log.debug("signalControllerStart: replying to request (sig id %s) - " % signal.uid)
        messenger.reply(signal, rc)


    def signalControllerStop(self, signal, sender, **data):
        """
        Called to handle the EVT_DIRECTOR_CTRLSTOP signal, which 
        is used to return the result of a stop command. 
        
        :param data['data]: This will contain the name of the
        controller to be started. This name is the same name
        as that in the configuration section.
        
        :returns: a call result dict.
            
            rc['result'] = 'ok' | 'error'
        
            For ok result:
            
            rc['data'] = ''
            
            For error result:
            
            rc['data'] = 'Error / Exception message'

        Note: this will contain every controller except the 
        director controller.
            
        Event Dispatched: EVT_DIRECTOR_CTRLSTOP

        """
        name = data['data']
        msg = ''
        try:
            self.log.debug("signalControllerStop: received request (sig id %s)." % signal.uid)
    
            c = director.config.get_cfg()
            for ctrl in c.cfg:
                if ctrl.name == name:
                    if ctrl.disabled == "yes":
                        msg = "The controller '%s' is disabled and cannot be stopped" % name
                    else:
                        ctrl.mod.stop()
                        msg = ctrl.mod.isStopped()
                    
                    break

        except:
            self.log.exception("signalControllerStop: error handling signal (sig id %s) - " % signal.uid)
            msg = self.formatError()
            rc = self.resultDict(msg)

        else:
            rc = self.resultDict(msg)

        self.log.debug("signalControllerStop: replying to request (sig id %s) - " % signal.uid)
        messenger.reply(signal, rc)


    def signalExit(self, signal, sender, **data):
        """
        Called to handle the EVT_EXIT_ALL signal, which tells
        the director to shutdown normally.
        
        """
        self.log.warn("main: EVT_EXIT_ALL received, exiting...")
        rc = self.resultDict('ok')
        messenger.reply(signal, rc)
        
        # allow time for message to reply of make its 
        # way out of director process if needs be.
        time.sleep(2)
        self.manager.exit()


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
        
        dispatcher.connect(
            self.signalControllerState,
            signal=messenger.EVT("EVT_DIRECTOR_CTRLSTATE")
        )        
        
        dispatcher.connect(
            self.signalControllerStart,
            signal=messenger.EVT("EVT_DIRECTOR_CTRLSTART")
        )        
        
        dispatcher.connect(
            self.signalControllerStop,
            signal=messenger.EVT("EVT_DIRECTOR_CTRLSTOP")
        )        
        
        # Register messenger hook for shutdown()
        dispatcher.connect(
            self.signalExit,
            signal=messenger.EVT("EVT_EXIT_ALL")
        )        
        self.log.info("signalSetup: EVT_EXIT_ALL signal setup.")

