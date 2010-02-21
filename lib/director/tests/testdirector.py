"""
"""
import os
import sys
import pprint
import os.path
import unittest

import tempfile

import director
import messenger
from director import signals
from messenger.testing import message_main
from director.testing import director_setup


class DirectorTC(unittest.TestCase):

    def cleanUp(self, top):
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                #print 'name:',name
                os.remove(os.path.join(root, name))
            for name in dirs:
                #print 'dir name:',name
                os.rmdir(os.path.join(root, name))


    def makeController(self, my_controller):
        p = tempfile.mkdtemp()
        sys.path.append(p)
        
        # Create a controller I can play with and test
        # the director behaviour with.
        #
        mypkg = os.path.join(p,'mypackage')
        os.mkdir(mypkg)
        
        f = os.path.join(mypkg, '__init__.py')
        fd = open(f, 'wb')
        fd.write("\n")
        fd.close()
        
        # Create an agent module that import_module should find and load.
        #
        f = os.path.join(mypkg, 'mycontroller.py')
        fd = open(f, 'wb')
        fd.write(my_controller)
        fd.close()
        
        return p


    def testControllerStartStopRestart(self):
        """Test a ping signal to the director.
        """
        my_controller = r"""
from director.controllers import base

class Controller(base.Controller):

    def setUp(self, config):
        base.Controller.setUp(self, config)
        self.startCalled = False
        self.stopCalled = False
        self.tearDownCalled = False
        self.isStartedCheck = False
        self.isStoppedCheck = False
        self.extraArg = config.get('extra_arg')

    def start(self):
        self.startCalled = True

    def isStarted(self):
        return self.isStartedCheck

    def stop(self):
        self.stopCalled = True

    def isStopped(self):
        return self.isStoppedCheck

    def tearDown(self):
        self.tearDownCalled = True

        """
        pkg_path = self.makeController(my_controller)
        
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
        
        [mycontroller]
        #disabled = 'yes'
        order = 8
        controller = 'mypackage.mycontroller'
        extra_arg = 'hello there'
        
        """
        m = director_setup(test_config)
        
        def testmain(tc):
            """Start-Stop-Restart"""
            # The configuration should contain the director and
            # controller with the load module instance from our
            # test controller
            #
            c = director.config.get_cfg()
            self.assertNotEquals(c.director, None)
            self.assertEquals(len(c.cfg), 2)
            
            # Quick ping to see if messaging is up and running:
            d = signals.SignalsSender()
            d.ping()
            
            # Check the initial state of our test controller. Its
            # loaded under a partial director. This is missing the
            # start although each controller will have had its setUp
            # called. We'll take card of running the controller via
            # signalling.
            #
            ctrl = c.cfg[1]
            self.assertEquals(ctrl.disabled, 'no')
            self.assertEquals(ctrl.order, 8)
            self.assertEquals(ctrl.controller, 'mypackage.mycontroller')
            self.assertNotEquals(ctrl.mod, None)
            self.assertEquals(ctrl.extra_arg, 'hello there')
            
            self.assertEquals(ctrl.mod.startCalled, False)
            self.assertEquals(ctrl.mod.stopCalled, False)
            self.assertEquals(ctrl.mod.tearDownCalled, False)
            self.assertEquals(ctrl.mod.isStartedCheck, False)
            self.assertEquals(ctrl.mod.isStoppedCheck, False)
            self.assertEquals(ctrl.mod.extraArg, 'hello there')

            def err_msg(correct, rc):
                return """rc != correct
                
                correct:
                %s
                
                rc:
                %s
                
                """ % (pprint.pformat(correct),pprint.pformat(rc))


            # Recover the current state of the controllers:
            #
            print "Calling controllerState..."
            rc = d.controllerState()
            self.assertEquals(rc['result'], 'ok')
            
            correct = [
                # The director won't appear in this list although its technically 
                # a controller.
                dict(name='mycontroller', disabled='no', started=False, config=ctrl.mod.config),
            ]
            
            self.assertEquals(len(rc['data']), 1)
            self.assertEquals(rc['data'], correct, err_msg(correct, rc['data']))


            # Tell the controller to start and check it is:
            #
            print "Calling controllerStart..."
            rc = d.controllerStart('mycontroller')
            self.assertEquals(rc['result'], 'ok', rc['data'])
            
            print "Calling controllerState..."
            rc = d.controllerState()
            self.assertEquals(rc['result'], 'ok')
            
            correct = [
                dict(name='mycontroller', disabled='no', started=True, config=ctrl.mod.config),
            ]
            
            self.assertEquals(rc['data'], correct, err_msg(correct, rc['data']))
            
            c = director.config.get_cfg()
            self.assertEquals(ctrl.mod.startCalled, True)
            self.assertEquals(ctrl.mod.stopCalled, False)


            # Tell the controller to stop and check it is:
            #
            print "Calling controllerStop..."
            rc = d.controllerStart('mycontroller')
            self.assertEquals(rc['result'], 'ok')
            
            print "Calling controllerState..."
            rc = d.controllerState()
            self.assertEquals(rc['result'], 'ok')
            
            correct = [
                dict(name='mycontroller', disabled='no', started=True, config=ctrl.mod.config),
            ]
            
            self.assertEquals(rc['data'], correct, err_msg(correct, rc['data']))
            
            c = director.config.get_cfg()
            self.assertEquals(ctrl.mod.startCalled, True)
            self.assertEquals(ctrl.mod.stopCalled, True)
            

        try:
            # Run inside the messaging system:
            message_main(self, testmain, cfg=messenger.default_config['stomp'])
            
        except:
            self.cleanUp(pkg_path)
            raise


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
            d = signals.SignalsSender()
            d.ping()
       
            
        # Run inside the messaging system:
        message_main(self, testmain, cfg=messenger.default_config['stomp'])


