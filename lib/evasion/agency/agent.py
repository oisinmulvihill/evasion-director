# -*- coding: utf-8 -*-
"""
:mod:`agency.agent`
====================

.. module:: 'agency.agent'
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the base agent interface.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module implements the base agent interface that agents must inherit from
and implement. The agent manager looks for this and if found uses it to create
and run the agent.

.. autoclass:: agency.agent.Base
   :members:
   :undoc-members:

"""
import logging


class Base(object):
    """Base class agent entry.
    """
    def __init__(self):
        self.log = logging.getLogger("evasion.agency.agent.Base")

    def setUp(self, config):
        """Called to set up the agent and subscribe for any events
        it may be interested in.

        """

    def tearDown(self):
        """Called to cleanup and release any resources the agent
        may be using.

        This is usually done by the agent manager before the
        program using it exits.

        """

    def start(self):
        """Called to start any processing the agent may need to do.

        This function maybe used to start any threads polling a
        agent for example.

        """

    def stop(self):
        """Called to stop any processing the agent may be doing.

        The start function may be called to resume operation.

        """
