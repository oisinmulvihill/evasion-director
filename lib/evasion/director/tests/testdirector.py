"""
"""
import os
import sys
import pprint
import logging
import os.path
import unittest
import tempfile

import nose

from evasion import director
from evasion import messenger
from evasion.director import config
from evasion.director import signals
from evasion.messenger.testing import message_main
from evasion.director.testing import director_setup


def get_log():
    return logging.getLogger('evasion.director.tests.testdirector')


def err_msg(correct, rc):
    return """rc != correct

    correct:
    %s

    rc:
    %s

    """ % (pprint.pformat(correct), pprint.pformat(rc))


class DirectorTC(unittest.TestCase):

    def cleanUp(self, top):
        get_log().warn("DirectorTC.cleanUp: cleaning here '%s'." % top)
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                #print 'name:',name
                os.remove(os.path.join(root, name))
            for name in dirs:
                #print 'dir name:',name
                os.rmdir(os.path.join(root, name))

    def makeController(self, my_controller, my_agent=None):
        p = tempfile.mkdtemp()
        sys.path.append(p)
        get_log().debug("DirectorTC.makeController: test package location '%s'." % p)

        # Create a controller I can play with and test
        # the director behaviour with.
        #
        mypkg = os.path.join(p, 'mypackage')
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

        if my_agent:
            f = os.path.join(mypkg, 'myagent.py')
            fd = open(f, 'wb')
            fd.write(my_agent)
            fd.close()

        return p

    def testControllerConfigRecovery(self):
        """Test the controller config recovery.
        """
        raise nose.SkipTest("Signal system needs sorting out.")

        my_controller = r"""
import logging
from evasion.director.controllers import base

def get_log():
    return logging.getLogger('evasion.director.tests.testdirector')

class Controller(base.Controller):

    def setUp(self, config):
        base.Controller.setUp(self, config)
        self.startCalled = False
        self.stopCalled = False
        self.tearDownCalled = False
        self.isStartedCheck = False
        self.isStoppedCheck = False
        self.extraArg = config.get('extra_arg')
        get_log().info('Controller: Setup Called!')

    def start(self):
        self.startCalled = True
        self.isStartedCheck = True
        get_log().info('Controller: start Called!')

    def isStarted(self):
        get_log().info('Controller: isStarted Called <%s>!' % self.isStartedCheck)
        return self.isStartedCheck

    def stop(self):
        self.stopCalled = True
        self.isStoppedCheck = True
        get_log().info('Controller: stop Called!')

    def isStopped(self):
        get_log().info('Controller: isStopped Called <%s>!' % self.isStoppedCheck)
        return self.isStoppedCheck

    def tearDown(self):
        self.tearDownCalled = True
        get_log().info('Controller: tearDown Called!')

        """

        my_agent = r"""
import logging
from evasion.agency import agent

def get_log():
    return logging.getLogger('evasion.director.tests.testdirector.testControllerConfigRecovery')

class Agent(agent.Base):

    def setUp(self, config):
        self.tearDownCalled = False
        self.startCalled = False
        self.stopCalled = False

    def tearDown(self):
        self.tearDownCalled = True

    def start(self):
        self.startCalled = True

    def stop(self):
        self.stopCalled = True

        """
        self.makeController(my_controller, my_agent)

        test_config = """
        [director]
        msg_host = '%(broker_interface)s'
        msg_port = %(broker_port)s
        msg_username = ''
        msg_password = ''
        msg_channel = '%(broker_channel)s'
        msg_interface = '%(broker_interface)s'
        proxy_dispatch_port = %(proxy_port)s

        # sets up a broker running when twisted runs:
        internal_broker = 'yes'

        [agency]
        #disabled = 'yes'
        order = 1

            [fancyagent]
            #disabled = 'yes'
            order = 1
            cat = 'general'
            agent = 'mypackage.myagent'

        [mycontroller]
        #disabled = 'yes'
        order = 4
        controller = 'mypackage.mycontroller'
        extra_arg = 'hello there'

        """
        director_setup(test_config)

        def testmain(tc):
            """"""
            c = config.get_cfg()
            self.assertNotEquals(c.director, None)
            self.assertNotEquals(c.agency, None)
            self.assertEquals(len(c.cfg), 3)
            self.assertEquals(len(c.agency.agents), 1)

            # Quick ping to see if messaging is up and running:
            d = signals.SignalsSender()
            get_log().info("testControllerConfigReload: calling ping")
            d.ping()

            # Check the initial state of our test controller.
            #
            ctrl = c.cfg[2]
            self.assertEquals(ctrl.disabled, 'no')
            self.assertEquals(ctrl.order, 4)
            self.assertEquals(ctrl.controller, 'mypackage.mycontroller')
            self.assertNotEquals(ctrl.mod, None)
            self.assertEquals(ctrl.extra_arg, 'hello there')

            # Called to return a version of the config that
            # could be pickled and transported externally.
            # The main difference will be no module code will
            # be exported as it won't pickle.
            #
            rc = d.configuration()
            self.assertEquals(rc['result'], 'ok')

            import pprint
            get_log().debug("""


            rc['data']

            %s


            """ % (pprint.pformat(rc['data'])))

        # Run inside the messaging system:
        message_main(self, testmain, cfg=messenger.default_config['stomp'])

    def testControllerConfigReload(self):
        """Test the reloading of a new controller configuration.
        """
        raise nose.SkipTest("Signal system needs sorting out.")

        my_controller = r"""
import logging
from evasion.director.controllers import base

def get_log():
    return logging.getLogger('evasion.director.tests.testdirector')

class Controller(base.Controller):

    def setUp(self, config):
        base.Controller.setUp(self, config)
        self.startCalled = False
        self.stopCalled = False
        self.tearDownCalled = False
        self.isStartedCheck = False
        self.isStoppedCheck = False
        self.extraArg = config.get('extra_arg')
        get_log().info('Controller: Setup Called!')

    def start(self):
        self.startCalled = True
        self.isStartedCheck = True
        get_log().info('Controller: start Called!')

    def isStarted(self):
        get_log().info('Controller: isStarted Called <%s>!' % self.isStartedCheck)
        return self.isStartedCheck

    def stop(self):
        self.stopCalled = True
        self.isStoppedCheck = True
        get_log().info('Controller: stop Called!')

    def isStopped(self):
        get_log().info('Controller: isStopped Called <%s>!' % self.isStoppedCheck)
        return self.isStoppedCheck

    def tearDown(self):
        self.tearDownCalled = True
        get_log().info('Controller: tearDown Called!')

        """
        pkg_path = self.makeController(my_controller)

        # Create a second controller which we'll use in the new
        # configuration.
        #
        my_controller2 = r"""
import logging
from evasion.director.controllers import base

def get_log():
    return logging.getLogger('evasion.director.tests.testdirector')

class Controller(base.Controller):

    def setUp(self, config):
        base.Controller.setUp(self, config)
        self.startCalled = False
        self.stopCalled = False
        self.tearDownCalled = False
        self.isStartedCheck = False
        self.isStoppedCheck = False

    def start(self):
        self.startCalled = True
        self.isStartedCheck = True
        get_log().info('Controller2: start Called!')

    def isStarted(self):
        get_log().info('Controller2: isStarted Called <%s>!' % self.isStartedCheck)
        return self.isStartedCheck

    def stop(self):
        self.stopCalled = True
        self.isStoppedCheck = True
        get_log().info('Controller2: stop Called!')

    def isStopped(self):
        get_log().info('Controller2: isStopped Called <%s>!' % self.isStoppedCheck)
        return self.isStoppedCheck

    def tearDown(self):
        self.tearDownCalled = True
        get_log().info('Controller2: tearDown Called!')

        """
        f = os.path.join(pkg_path, 'mypackage', 'mycontroller2.py')
        fd = open(f, 'wb')
        fd.write(my_controller2)
        fd.close()

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
        director_setup(test_config)

        def testmain(tc):
            """Start-Stop-Restart"""
            # The configuration should contain the director and
            # controller with the load module instance from our
            # test controller
            #
            c = config.get_cfg()
            self.assertNotEquals(c.director, None)
            self.assertEquals(len(c.cfg), 2)

            # Quick ping to see if messaging is up and running:
            d = signals.SignalsSender()
            get_log().info("testControllerConfigReload: calling ping")
            d.ping()

            # Check the initial state of our test controller.
            #
            ctrl = c.cfg[1]
            self.assertEquals(ctrl.disabled, 'no')
            self.assertEquals(ctrl.order, 8)
            self.assertEquals(ctrl.controller, 'mypackage.mycontroller')
            self.assertNotEquals(ctrl.mod, None)
            self.assertEquals(ctrl.extra_arg, 'hello there')

            original_ctrl = ctrl.mod
            self.assertEquals(ctrl.mod.startCalled, False)
            self.assertEquals(ctrl.mod.stopCalled, False)
            self.assertEquals(ctrl.mod.tearDownCalled, False)
            self.assertEquals(ctrl.mod.isStartedCheck, False)
            self.assertEquals(ctrl.mod.isStoppedCheck, False)
            self.assertEquals(ctrl.mod.extraArg, 'hello there')

            # Start the controller before we do a reload
            #
            get_log().info("testControllerConfigReload 0. Calling controllerStart...")
            rc = d.controllerStart('mycontroller')
            self.assertEquals(rc['result'], 'ok')
            self.assertEquals(rc['data'], True)

            # Create the new configuration and then tell the
            # controller to reload it. This should cause the
            # running controller to be stopped. The tearDown
            # method will also be called. The controller
            # name cannot be changed. This is used to refer to
            # the original configuration section. It is needed
            # when saving the configuration to disk.
            #
            # This configuration replaces what was there.
            new_config = dict(
                order=4,
                name="mycontroller",
                disabled='no',
                controller='mypackage.mycontroller2'
            )

            # Do the reload:
            rc = d.controllerReload('mycontroller', new_config)
            self.assertEquals(rc['result'], 'ok')
            self.assertEquals(rc['data'], True)

            # Check controller is different and that the original
            # controller got shutdown correctly:
            self.assertEquals(original_ctrl.startCalled, True)
            self.assertEquals(original_ctrl.stopCalled, True)
            self.assertEquals(original_ctrl.tearDownCalled, True)

            # Get the newly updated configuration and check the
            # new controllers state.
            #
            c = config.get_cfg()
            ctrl = c.cfg[1]
            self.assertNotEquals(ctrl, original_ctrl)
            self.assertNotEquals(c.director, None)
            self.assertEquals(len(c.cfg), 2)

            # Check out the new controller state:
            #
            self.assertEquals(ctrl.mod.startCalled, False)
            self.assertEquals(ctrl.mod.stopCalled, False)
            self.assertEquals(ctrl.mod.tearDownCalled, False)
            self.assertEquals(ctrl.mod.isStartedCheck, False)
            self.assertEquals(ctrl.mod.isStoppedCheck, False)
            self.assertEquals(hasattr(ctrl.mod, 'extraArg'), False)

        # Huzzagh!
        try:
            # Run inside the messaging system:
            message_main(self, testmain, cfg=messenger.default_config['stomp'])

        except:
            self.cleanUp(pkg_path)
            raise

    def testControllerStartStop(self):
        """Test starting and stopping a loaded controller.
        """
        raise nose.SkipTest("Signal system needs sorting out.")

        my_controller = r"""
import logging
from evasion.director.controllers import base

def get_log():
    return logging.getLogger('evasion.director.tests.testdirector')

class Controller(base.Controller):

    def setUp(self, config):
        base.Controller.setUp(self, config)
        self.startCalled = False
        self.stopCalled = False
        self.tearDownCalled = False
        self.isStartedCheck = False
        self.isStoppedCheck = False
        self.extraArg = config.get('extra_arg')
        get_log().info('Controller: Setup Called!')

    def start(self):
        self.startCalled = True
        self.isStartedCheck = True
        get_log().info('Controller: start Called!')

    def isStarted(self):
        get_log().info('Controller: isStarted Called <%s>!' % self.isStartedCheck)
        return self.isStartedCheck

    def stop(self):
        self.stopCalled = True
        self.isStoppedCheck = True
        get_log().info('Controller: stop Called!')

    def isStopped(self):
        get_log().info('Controller: isStopped Called <%s>!' % self.isStoppedCheck)
        return self.isStoppedCheck

    def tearDown(self):
        self.tearDownCalled = True
        get_log().info('Controller: tearDown Called!')

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
        director_setup(test_config)

        def testmain(tc):
            """Start-Stop-Restart"""
            # The configuration should contain the director and
            # controller with the load module instance from our
            # test controller
            #
            c = config.get_cfg()
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
            self.assertEquals(rc['result'], 'ok')
            self.assertEquals(rc['data'], True)

            print "Calling controllerState..."
            rc = d.controllerState()
            self.assertEquals(rc['result'], 'ok')

            correct = [
                dict(name='mycontroller', disabled='no', started=True, config=ctrl.mod.config),
            ]

            self.assertEquals(rc['data'], correct, err_msg(correct, rc['data']))

            c = config.get_cfg()
            self.assertEquals(ctrl.mod.startCalled, True)
            self.assertEquals(ctrl.mod.stopCalled, False)

            # Tell the controller to stop and check it is:
            #
            print "Calling controllerStop..."
            rc = d.controllerStop('mycontroller')
            self.assertEquals(rc['result'], 'ok')
            self.assertEquals(rc['data'], True)

            print "Calling controllerState..."
            rc = d.controllerState()
            self.assertEquals(rc['result'], 'ok')

            correct = [
                dict(name='mycontroller', disabled='no', started=True, config=ctrl.mod.config),
            ]

            self.assertEquals(rc['data'], correct, err_msg(correct, rc['data']))

            c = config.get_cfg()
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
        raise nose.SkipTest("Signal system needs sorting out.")

        test_config = """
        [director]
        messaging = yes
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
        director_setup(test_config)

        def testmain(tc):
            """This should ping without raising a timeout exceptions"""
            d = signals.SignalsSender()
            d.ping()

        # Run inside the messaging system:
        message_main(self, testmain, cfg=messenger.default_config['stomp'])
