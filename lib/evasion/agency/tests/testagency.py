# -*- coding: utf-8 -*-
"""
"""
import unittest

from evasion import agency
from evasion.director import config
from evasion.director.testing import director_setup


class AgencyTC(unittest.TestCase):

    def setUp(self):
        # unittesting reset:
        agency.node._reset()

    def testagencyNodes(self):
        """Test the agent node id generation.
        """

        # check that all the agent nodes have no entries:
        for cat in agency.AGENT_CATEGORIES:
            count = agency.node.get(cat)
            self.assertEquals(count, 0)

        self.assertRaises(ValueError, agency.node.add, 'unknown agent class', 'testing' ,'1')

        # test generation of new ids
        node_id, alias_id = agency.node.add('swipe', 'testing', '12')
        self.assertEquals(node_id, '/agent/swipe/testing/1')
        self.assertEquals(alias_id, '/agent/swipe/12')

        node_id, alias_id = agency.node.add('swipe', 'testing', '23')
        self.assertEquals(node_id, '/agent/swipe/testing/2')
        self.assertEquals(alias_id, '/agent/swipe/23')



