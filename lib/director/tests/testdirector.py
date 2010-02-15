import pprint
import unittest

import director

testcfg = """
[director] 
somevalue = 123
"""

class DirectorTC(unittest.TestCase):


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



