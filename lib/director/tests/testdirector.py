import unittest

import director


class DirectorTC(unittest.TestCase):

    def testProgramModuleLoading(self):
        """
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
        director.config.load(test_config)
        
