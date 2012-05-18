"""
:mod:`manager` -- Main director control code.
==============================================

.. module:: evasion.director
   :platform: Unix, MacOSX, Windows
   :synopsis: Main director control code.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: evasion.director.manager.Manager
   :members:
   :undoc-members:

"""
import sys
import time
import logging
import traceback

NO_MESSAGING = False
try:
    from evasion import messenger
    from evasion.director import signals

except ImportError:
    # disable messaging, this will get logged later.
    # The evasion-messenger is not installed.
    NO_MESSAGING = True
    sys.stdout.write("evasion.messenger not present. Messaging disabled.\n")

from evasion.director import config

try:
    import decorator  # help for bbfreeze.
except ImportError, e:
    pass


def get_log():
    return logging.getLogger("evasion.director.manager")


class Manager(object):
    """Manages the running services determined by the configuration
    that was loaded.

    The manager expects to find a [director] section in the configuration.
    For more on this see director.configobjs.Director doc string.

    """
    log = logging.getLogger("evasion.director.manager.Manager")

    def __init__(self, eat_exceptions=False):
        """

        :param eat_exceptions: True | False (default).

        If True the director will attempt to keep going with controller
        exceptions. All exceptions get logged regardless.

        """
        self.controllers = []
        if not NO_MESSAGING:
            self.log.warn("Messaging disable as evasion-messenger is not installed.")
            self.signals = signals.SignalsReceiver(self)
        else:
            self.signals = None
        self.nameLookup = {}
        self.eat_agent_exceptions = eat_exceptions

    def keep_going_on_exceptions(self):
        """Return the state of eat_agent_exceptions True | False."""
        return self.eat_agent_exceptions

    def controller(self, name):
        """Called to recover a loaded controller based on the given name.

        The name lookup is only set up after controllerSetup() has
        been called.

        KeyError will be raised if no entry for the given name was
        found.

        :returns: The loaded instance implementing Controller.

        This will be the Controller instace from the config:

            controller = '<package string>'

        """
        return self.nameLookup[name].mod

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
        c = config.get_cfg()

        # Recover and import the controllers:
        self.controllers = config.load_controllers(c.cfg, ignore_exceptions=True)
        self.log.info("controllerSetup: %s controller(s) recovered." % len(self.controllers))

        if self.controllers:
            # Setup all enabled controllers:
            for ctl in self.controllers:
                self.nameLookup[ctl.name] = ctl
                controller = ctl.mod
                if not controller:
                    self.log.warn("controllerSetup: %s module isn't loaded!" % ctl)
                    continue
                try:
                    if ctl.disabled == 'no':
                        controller.setUp(ctl.config)
                except:
                    self.log.exception("%s setUp error: " % ctl)
                    sys.stderr.write("%s setUp error: %s" % (ctl, self.formatError()))
                    if not self.keep_going_on_exceptions():
                        # Stop!
                        raise
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
                self.log.warn("tearDown: %s module isn't loaded!" % ctl)
                continue
            try:
                controller.stop()
            except:
                self.log.exception("%s stop error: " % ctl)
                sys.stderr.write("%s stop error: %s" % (ctl, self.formatError()))
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise

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
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise

    def appmainSetup(self):
        """
        Called from appmain or from testing to set up the signal
        handling and other items ready for a run / test run.

        :returns: poll_time used by the director as a sleep
        between controller checks.

        """
        c = config.get_cfg()
        poll_time = float(c.director.poll_time)

        if not NO_MESSAGING:
            # Set up all signals handlers provided by the director:
            self.signals.setup()

        # Recover the controllers from director configuration.
        self.controllerSetup()

        return poll_time

    def step(self):
        """Perform a single pass through the controllers maintenance steps.

        This is used by appmain or from the tests.

        """
        # Check the controllers are alive and restat if needs be:
        for ctl in self.controllers:
            if ctl.wasStopped and ctl.mod:
                if ctl.mod.isStarted():
                    self.log.info("appmain: The controller '%s' needs to be stopped." % (ctl))
                    ctl.mod.stop()
                    self.log.info("appmain: The controller '%s' stop has been called." % (ctl))

            elif ctl.disabled == 'no' and ctl.mod:
                try:
                    if not ctl.mod.isStarted():
                        self.log.info("appmain: The controller '%s' needs to be started." % (ctl))
                        ctl.mod.start()
                        rc = ctl.mod.isStarted()
                        self.log.info("appmain: Started ok '%s'? '%s'" % (ctl.name, rc))
                except (SystemExit, KeyboardInterrupt):
                    raise
                except:
                    self.log.exception("%s appmain error: " % ctl)
                    sys.stderr.write("%s appmain error: %s" % (ctl, self.formatError()))
                    if not self.keep_going_on_exceptions():
                        # Stop!
                        self.log.exception("Shutting down now on exception in: %s " % ctl)
                        self.exit()

    def appmain(self, isExit):
        """
        Run the main program loop.

        :param isExit: This is a function that will return true
        when its time to exit.

        Note: this is a thread which we are running in and the
        messenger will determine when its time to exit.

        """
        # Perform signal, controller, etc setup
        poll_time = self.appmainSetup()

        while not isExit():
            self.step()

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

    def main(self, director_testing=False):
        """
        The main thread in which twisted and the messagin system runs. The
        manager main run inside its own thread. The appman(...) is the
        main of the director.

        """
        self.log.info("main: running.")
        c = config.get_cfg()

        class ExitTime(object):
            def __init__(self):
                self.exitTime = False

            def isExit(self):
                return self.exitTime

        et = ExitTime()

        # Allow twisted to be disable if no messaging is used or an alternative
        # approach is used.
        if NO_MESSAGING or c.director.messaging == 'no':
            try:
                self.appmain(et.isExit)

            except KeyboardInterrupt:
                self.log.warn("Ctrl-C, Exiting.")

            except:
                self.log.exception("Exiting on exception: ")

            finally:
                # Indicate the director should exit then call shutdown to
                # cleanly tell all controllers to shutdown as well
                et.exitTime = True
                self.shutdown()

        else:
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

            # Use internal broker? This allow simplifies things and
            # means we don't have to run a morbid/other program as
            # a child process.
            #
            if c.director.internal_broker == 'yes':
                self.log.warn("main: Starting the interal light weight broker (internal_broker = 'yes').")
                from evasion.director import testing
                testing.setup_broker(
                    int(c.director.msg_port),
                    c.director.msg_interface
                )

            noproxydispatchbroker = c.director.noproxydispatch
            if noproxydispatchbroker == 'no':
                from evasion.director import proxydispatch

                port = int(c.director.proxy_dispatch_port)
                self.log.info("main: setting up reply proxy dispatch http://127.0.0.1:%s/ ." % port)
                proxydispatch.setup(port)

            else:
                self.log.warn("main: the director's proxydispatch is disabled (noproxydispatch = 'yes').")

            if director_testing:
                self.log.warn("main: testing active! The main loop is running elsewhere.")

            else:
                try:
                    self.log.info("main: Running.")
                    messenger.run(self.appmain)

                finally:
                    self.log.info("main: shutdown!")
                    self.shutdown()
                    self.exit()
