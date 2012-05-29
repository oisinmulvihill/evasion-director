# -*- coding: utf-8 -*-
"""
:mod:`manager` -- This supervises then agents under its control.
=================================================================

.. module:: manager
   :platform: Unix, MacOSX, Windows
   :synopsis: This supervises then agents under its control.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This is the manager. It is reposible for managing the physical agents the
application is using. The agent manager takes care of the loading and
intialisation of each agent, using the configuration provided by the user.

.. exception:: evasion.agency.manager.ManagerError

.. autoclass:: evasion.agency.manager.Manager
   :members:
   :undoc-members:


"""
import sys
import logging
import traceback


import agency


def get_log():
    return logging.getLogger('evasion.agency.manager')


class ManagerError(Exception):
    """Raised for problems occuring in the agent manager.
    """


class Manager(object):
    """The agent manager takes care of the load of agents and
    provides a central point to setUp, tearDown, start & stop
    all agent nodes under our care.

    """
    def __init__(self, eat_agent_exceptions=False):
        """

        :param eat_agent_exceptions: True | False (default).

        If this is True then all attempts will be made to keep going in
        setUp, tearDown, start and stop. All exceptions will be logged to
        logging and to stderr.

        """
        self.log = logging.getLogger('evasion.agency.manager.Manager')
        self._agents = {}
        self.eat_agent_exceptions = eat_agent_exceptions

    def keep_going_on_exceptions(self):
        """Return the state of eat_agent_exceptions True | False."""
        return self.eat_agent_exceptions

    def getAgentCount(self):
        return len(self._agents.keys())

    agents = property(getAgentCount)

    def shutdown(self):
        """Used to tearDown and reset the internal state of the agent
        manager ready for a new load command.

        """
        # Close and free any resources we may be using and clear out state.
        try:
            self.tearDown()
        except ManagerError:
            pass
        self._agents = {}

    def agent(self, alias, absolute=False):
        """Called to recover a specific agent node.

        alias:
            This is the alias for a specific agent
            node stored in the agent manager.


        If the alias is not found the ManagerError
        will be raised.

        """
        #print "self._agents:"
        #import pprint
        #pprint.pprint(self._agents)
        #print

        full_alias = alias
        if not absolute:
            full_alias = '/agent/%s' % alias

        #print "looking for: ", full_alias
        if not full_alias in self._agents:
            raise ManagerError("The agent node alias '%s' was not found!" % full_alias)

        return self._agents[full_alias]

    def load(self):
        """Load the agent modules into the system wide configuration.

        The system wide configuration needs to have been set up
        via the director.config functions.

        The shutdown method must be called before recalling load.
        If this has not been done then ManagerError will be raised.

        returned:
            For testing purposes the loaded list of agents . This
            shouldn't be used normally.

        """
        if self.agents > 0:
            raise ManagerError("Load has been called already! Please call shutdown first!")

        # Lazy import to prevent circular imports.
        from evasion import director

        # Recover the configuration and load in the agent modules
        # which are currently enabled.
        c = director.config.get_cfg()
        cfg_objs = director.config.load_agents(c.cfg)
        director.config.update_objs(cfg_objs)
        c = director.config.get_cfg()

        if not c.agency:
            self.log.warn("load: No agency is present to load agents for.")
            return []

        # Store the agents we're running here in an addressable form.
        alias_check = {}
        for a in c.agency.agents:
            a.node, a.alias = agency.node.add(a.cat, a.name, a.alias)
            if alias_check.get(a.alias, 0):
                bad = a.alias.split('/')[-1]
                raise ManagerError("A duplicate config alias '%s' has been found for '%s'" % (
                    bad, a.name
                ))
            else:
                alias_check[a.alias] = 1

            self._agents[a.alias] = a

        self.log.info("load: %s agent(s) present." % self.getAgentCount())

        return c.agency.agents

    def formatError(self):
        """Return a string representing the last traceback.
        """
        exception, instance, tb = traceback.sys.exc_info()
        error = "".join(traceback.format_tb(tb))
        return error

    def setUp(self):
        """Called to initialise all agents in our care.

        The load method must be called before this one.
        Otherwise ManagerError will be raised.

        """
        if self.agents < 1:
            self.log.warn("There are no agents to set up.")
            return

        for a in self._agents.values():
            if a.disabled == 'yes' or not a.mod:
                # skip this agent.
                continue
            try:
                a.mod.setUp(a.config)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.log.exception("%s setUp error: " % a)
                sys.stderr.write("%s setUp error: %s" % (a, self.formatError()))
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise

    def tearDown(self):
        """Called to tearDown all agents in our care.

        Before calling a agents tearDown() its stop()
        method is called first.

        The load method must be called before this one.
        Otherwise ManagerError will be raised.

        """
        if self.agents < 1:
            self.log.warn("There are no agents to tear down.")
            return

        for a in self._agents.values():
            if a.disabled == 'yes' or not a.mod:
                # skip this agent.
                continue
            try:
                a.mod.tearDown()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.log.exception("%s tearDown error: " % a)
                sys.stderr.write("%s tearDown error: %s" % (a, self.formatError()))
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise

    def start(self):
        """Start all agents under our management

        The load method must be called before this one.
        Otherwise ManagerError will be raised.

        """
        if self.agents < 1:
            self.log.warn("There are no agents to start.")
            return

        for a in self._agents.values():
            if a.disabled == 'yes' or not a.mod:
                # skip this agent.
                continue
            try:
                a.mod.start()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.log.exception("%s start error: " % a)
                sys.stderr.write("%s start error: %s" % (a, self.formatError()))
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise

    def stop(self):
        """Start all agents under our management

        The load method must be called before this one.
        Otherwise ManagerError will be raised.

        """
        if self.agents < 1:
            self.log.warn("There are no agents to stop.")
            return

        for a in self._agents.values():
            if a.disabled == 'yes' or not a.mod:
                # skip this agent.
                continue
            try:
                a.mod.stop()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.log.exception("%s stop error: " % a)
                sys.stderr.write("%s stop error: %s" % (a, self.formatError()))
                if not self.keep_going_on_exceptions():
                    # Stop!
                    raise
