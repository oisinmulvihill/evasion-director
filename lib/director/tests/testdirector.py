import unittest

import director

testcfg = """
[director] 
somevalue = 123
"""

class DirectorTC(unittest.TestCase):
    

    def testWebAdminConfigRecovery(self):
        """Test the parsing of the controllers to see that the webadmin modules are found or not as the case maybe.
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

        [echodir]
        order = 2
        controller = 'director.controllers.commandline'
        command = "echo 'hello' > /tmp/hello.txt"
        workingdir = "/tmp"

        [lsdir]
        order = 2
        controller = 'director.controllers.commandline'
        webadmin = listingadmin
        command = "ls 'hello' > /tmp/dirlisting.txt"
        workingdir = "/tmp"

        [myswipe]
        # Should ignore this too as its also not a program.
        cat = 'general'
        agent = 'agency.agents.testing.fake'
        something = 1
        
        """
        programs = director.config.load(test_config)
        self.assertEquals(len(programs), 2)
    
    
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



