"""
:mod:`agency`
==============

.. module:: 'agency'
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This `agency.agency` module provides the single manager instance used to store the Agent instances.
This module also provides the AGENT_CATEGORIES. These categories are used to group agents of common
functionality together. There is no rigid enforcement of which agent belongs where. They are only
used as a convention. These categories are the strings that are used in the class field in the
configuration.

.. data:: agency.agency.AGENT_CATEGORIES

.. autoclass:: agency.agency.Nodes
   :members:
   :undoc-members:

.. autofunction::  agency.agency.shutdown()

.. automodule:: agency.agency

.. automodule:: agency.agent

.. automodule:: agency.agents

.. automodule:: agency.manager

"""
import logging

import agent
import agency
import agents
import manager
from agency import *
from manager import ManagerError


def get_log():
    return logging.getLogger('agency')
