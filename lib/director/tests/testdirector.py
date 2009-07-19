import unittest

import director


class DirectorTC(unittest.TestCase):


    def testTestTheOrder(self):
        """
        """
        test_config = """
        [checkdir]
        disabled = 'no'
        order = 1
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"

        [echodir]
        disabled = 'yes'
        order = 2
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
        self.assertEquals(ctl.controller.__name__, 'Controller')
        self.assertEquals(ctl.command, 'ls')
        self.assertEquals(ctl.workingdir, '/tmp')

        order, ctl = programs[1]
        self.assertEquals(order, '2')
        self.assertEquals(ctl.order, '2')
        self.assertEquals(ctl.disabled, 'yes')
        self.assertEquals(ctl.controller.__name__, 'Controller')
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
        disabled = 'yes'
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



