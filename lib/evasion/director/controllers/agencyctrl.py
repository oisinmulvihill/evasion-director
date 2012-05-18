"""
:mod:`agency` -- This runs the agency without needing to spawnit under another python process.
=================================================================================================

.. module:: evasion.director.controllers.agencyctrl
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the interface to command line processes.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This runs the agency without needing to spawnit under another python process.

.. autoclass:: evasion.director.controllers.agencyctrl.Controller
   :members:
   :undoc-members:

"""
import logging

from evasion.agency.manager import Manager
from evasion.director.controllers import base


class Controller(base.Controller):
    """
    This controller typically has the following configuration::

        [agency]
        # Standard options example:
        controller = 'evasion.director.controllers.agencyctrl'

        # (OPTIONAL) Uncomment to prevent this controller
        # from being used. If the agency is disabled no agents
        # will be recovered from config or loaded.
        #disabled = 'yes'

        # (Optional) Log exceptions but keep going True | False (default):
        # eat_agent_exceptions = False

        # (OPTIONAL) When to start the agency. It should start after the
        # broker.
        order = 2

    The agency uses the director system wide config should be set
    up by the time setUp method is called.

    """
    log = logging.getLogger('evasion.director.controllers.agencyctrl')

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
        self.log.info("setUp: setting up the agency and recovering agents.")
        self.manager = Manager(
            eat_agent_exceptions=config.get('eat_agent_exceptions', False)
        )
        self.manager.load()
        self.manager.setUp()

        self.log.info("setUp: agents loaded '%d'." % self.manager.agents)

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
