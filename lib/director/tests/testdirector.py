import pprint
import unittest

import director

testcfg = """
[director] 
somevalue = 123
"""

class DirectorTC(unittest.TestCase):


    def testWebAdminConfigRecovery(self):
        """Test the parsing of the config recovering any webadmin modules mentioned.
        """
        test_config = """
        [director]
        # The broker connection details:
        msg_host = "127.0.0.1"
        msg_port = 61613
        msg_username = ''
        msg_password = ''
        msg_channel = 'newman'
        disable_broker = no
        poll_time = 1
        # This is the root level interface the webadmin will use if present:
        webadmin = 'director.webadmin'

        # anything can have a webadmin interface, I'm looking for the webadmin attribute:
        [messenger]
        host="localhost"
        port=61613
        webadmin = 'webadminbroker'
        
        [agencyhq]
        #disabled = 'yes'
        webadmin = 'agency.webadmin'

            # should show up as its got webadmin section and isn't disabled:
            [testingsale]
            #disabled = 'yes'
            cat = sale
            agent = devicelayer.agents.testing.sale
            interface = 127.0.0.1
            port = 54998
            webadmin = 'testsale'

            # This agent has no webadmin so won't be present in modules
            [testingprinter]
            #disabled = 'yes'
            cat = printer
            agent = devicelayer.agents.testing.printer
            #show_gui = 'yes'
            interface = 127.0.0.1
            port = 50980

            # This is disabled so its webadmin interface won't appear in modules:
            [testingfrog]
            disabled = 'yes'
            cat = swipe
            agent = myswipe
            webadmin = 'webadminprinter'

            [dog]
            #disabled = 'yes'
            cat = swipe
            agent = myswipe
            webadmin = 'webadmindog'

        [checkdir]
        order = 4
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"
        webadmin = 'bob.webadmin'

        [echodir]
        order = 5
        controller = 'director.controllers.commandline'
        command = "echo 'hello' > /tmp/hello.txt"
        workingdir = "/tmp"

        [lsdir]
        order = 6
        controller = 'director.controllers.commandline'
        webadmin = listingadmin
        command = "ls 'hello' > /tmp/dirlisting.txt"
        workingdir = "/tmp"
        
        """
        # Recover the webadmin module names if any are mentioned 
        # by the controllers.
        #
        module_names = director.config.webadmin_modules(test_config)
        
        correct = [
            dict(director='director',webadmin='director.webadmin'), 
            dict(messenger='messenger',webadmin='webadminbroker'),
            dict(agency='agencyhq',webadmin='agency.webadmin'),
            dict(agent='testingsale',webadmin='testsale'),
            dict(agent='dog',webadmin='webadmindog'),
            dict(controller='checkdir',webadmin='bob.webadmin'),
            dict(controller='lsdir',webadmin='listingadmin'),
        ]
       
        msg = """
        Recovery Failed, correct != recovered
        
        correct:
        %s
        
        found:
        %s
        
        """ % (pprint.pformat(correct), pprint.pformat(module_names))
        
        self.assertEquals(module_names, correct, msg)
        

    def testConfigContainers(self):
        """Test the contents of a loaded controller.
        """
        test_config = """
        [messenger]
        # not a controller, should be ignored.
        host="localhost"
        port=61613

        [checkdir]
        order = 1
        controller = 'director.controllers.commandline'
        webadmin = checkdiradmin
        command = "ls"
        workingdir = "/tmp"
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 1)
        
        order_position, entry = programs[0]
        
        self.assertEquals(order_position, '1')
        self.assertEquals(entry.name, 'checkdir')
        self.assertEquals(entry.order, '1')
        self.assertEquals(entry.disabled, 'no')        
        self.assertEquals(isinstance(entry.controller, director.controllers.commandline.Controller), True)        
        self.assertEquals(entry.webadmin, 'checkdiradmin')
        self.assertEquals(entry.workingdir, '/tmp')
        self.assertEquals(entry.command, 'ls')
    
    
    def testRequiredConfigSection(self):
        """Test that the evasion section is present in the given config file.
        """
        # Check that no setup done is caught:
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        testcfg = """
[director] 
somevalue = 123
"""
        director.config.set_cfg(testcfg)
        c = director.config.get_cfg()

        self.assertEquals(c.raw, testcfg)
        self.assertEquals(c.cfg['director']['somevalue'], '123')

        
    def testdirectorConfig(self):
        """Test the configuration set and machinery
        """
        # Reset and Check that no setup done is caught:
        director.config.clear()
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        director.config.set_cfg(testcfg)
        director.config.get_cfg()
        

    def testTestTheOrder(self):
        """Test the container instances which should be setup from configuration.
        """
        test_config = """
        [checkdir]
        disabled = 'no'
        order = 1
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"

        [echodir]
        # disabled = yes means module won't be loaded.
        disabled = 'yes'
        order = 2
        controller = 'director.controllers.commandline'
        command = "echo 'hello' > /tmp/hello.txt"
        workingdir = "/tmp"        

        [echodir-active]
        disabled = 'no'
        order = 3
        controller = 'director.controllers.commandline'
        command = "echo 'hello' > /tmp/hello.txt"
        workingdir = "/tmp"        
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 2)

        order, ctl = programs[0]
        self.assertEquals(order, '1')
        self.assertEquals(ctl.order, '1')
        self.assertEquals(ctl.disabled, 'no')
        self.assertEquals(ctl.command, 'ls')
        self.assertEquals(ctl.workingdir, '/tmp')

        order, ctl = programs[1]
        self.assertEquals(order, '3')
        self.assertEquals(ctl.order, '3')
        self.assertEquals(ctl.disabled, 'no')
        self.assertEquals(ctl.command, "echo 'hello' > /tmp/hello.txt")
        self.assertEquals(ctl.workingdir, '/tmp')


    def testProgramModuleLoading(self):
        """Test the parsing of the director configuration and its ignoring of non-contoller modules.
        """
        test_config = """
        [messenger]
        # not a controller, should be ignored.
        host="localhost"
        port=61613

        [checkdir]
        disabled = 'no'
        order = 1
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"

        [echodir]
        disabled = 'no'
        order = 2
        controller = 'director.controllers.commandline'
        command = "echo 'hello' > /tmp/hello.txt"
        workingdir = "/tmp"

        [myswipe]
        # Should ignore this too as its also not a program.
        cat = 'general'
        agent = 'agency.agents.testing.fake'
        something = 1
        
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 2)

        # Just check empty cases return:
        test_config = """
        [messenger]
        # not a controller, should be ignored.
        host="localhost"
        port=61613

        [myswipe]
        # Should ignore this too as its also not a program.
        cat = 'general'
        agent = 'agency.agents.testing.fake'
        something = 1
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 0)

        test_config = """
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 0)



