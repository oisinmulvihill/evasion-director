"""
"""
import pprint
import unittest

import director
import messenger
from director.signals import SignalsSender
from messenger.testing import message_main
from director.testing import director_setup


class DirectorTC(unittest.TestCase):


    def testPingSignal(self):
        """Test a ping signal to the director.
        """
        test_config = """
        [director]
        msg_host = '%(broker_interface)s'
        msg_port = %(broker_port)s
        msg_username = ''
        msg_password = ''
        msg_channel = 'evasion'
        msg_interface = '%(broker_interface)s'
        proxy_dispatch_port = %(proxy_port)s
        
        # sets up a broker running when twisted runs:
        internal_broker = 'yes'
        
        """
        m = director_setup(test_config)
        
        def testmain(tc):
            """This should ping without raising a timeout exceptions"""
            d = SignalsSender()
            d.ping()
       
            
        # Run inside the messaging system:
        message_main(self, testmain, cfg=messenger.default_config['stomp'])


