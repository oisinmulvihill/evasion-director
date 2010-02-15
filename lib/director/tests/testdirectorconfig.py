import pprint
import unittest

import director



class DirectorConfigTC(unittest.TestCase):
    """Exercise the director configuration functionality
    """
    
    def testWebAdminConfigRecovery(self):
        """Test the parsing of the config recovering any webadmin modules mentioned.
        """
        test_config = """
        [director]
        # This is the root level interface the webadmin will use if present:
        webadmin = 'director.webadmin'

        # anything can have a webadmin interface, I'm looking for the webadmin attribute:
        [broker]
        webadmin = 'webadminbroker'
        
        [agency]
        webadmin = 'agency.webadmin'

            # should show up as its got webadmin section and isn't disabled:
            [testingsale]
            cat = sale
            agent = devicelayer.agents.testing.sale
            webadmin = 'testsale'

            # This agent has no webadmin so won't be present in modules
            [testingprinter]
            cat = printer
            agent = devicelayer.agents.testing.printer

            # This is disabled so its webadmin interface won't appear in modules:
            [testingfrog]
            disabled = 'yes'
            cat = swipe
            agent = myswipe
            webadmin = 'webadminprinter'

            [dog]
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
        
        [somerandomsection]
        order = 10
        # This will become a catch all container object
        bob = '1234'
        uptime = True
        webadmin = 'bobadmin'
        
        """
        # Convert to config objects:
        objs = director.config.recover_objects(test_config)
        
        # Recover the webadmin module names if any are mentioned 
        # by the controllers.
        module_names = director.config.webadmin_modules(objs)
        
        correct = [
            dict(name='director',type='director',webadmin='director.webadmin'), 
            dict(name='broker',type='broker',webadmin='webadminbroker'),
            dict(name='agency',type='agency',webadmin='agency.webadmin'),
            dict(name='testingsale',type='agent',webadmin='testsale'),
            dict(name='dog',type='agent',webadmin='webadmindog'),
            dict(name='checkdir',type='controller',webadmin='bob.webadmin'),
            dict(name='lsdir',type='controller',webadmin='listingadmin'),
            dict(name='somerandomsection',type='container',webadmin='bobadmin'),
        ]
       
        msg = """
        Recovery Failed, correct != recovered
        
        correct:
        %s
        
        recovered:
        %s
        
        """ % (pprint.pformat(correct), pprint.pformat(module_names))
        
        self.assertEquals(module_names, correct, msg)


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
        testcfg = """
        [director] 
        somevalue = 123
        """
        
        # Reset and Check that no setup done is caught:
        director.config.clear()
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        director.config.set_cfg(testcfg)
        director.config.get_cfg()


    def testOrdering(self):
        """Test the ordering of configuration objects.
        """
        test_config = """
        [director]
        # The director is a hardcoded order of 0. The is not much 
        # point ordering before it as the director runs all the 
        # other parts and the order has no effect on it.
        
        [broker]
        order = 4
        
        [agency]
        order = 2

            [aardvark]
            order = 1
            cat = swipe
            agent = myswipe

            [bat]
            order = 0
            cat = swipe
            agent = myswipe

        [webadmin]
        order = 1

        [checkdir]
        order = 3
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"
        webadmin = 'bob.webadmin'

        """
        objs = director.config.recover_objects(test_config)
        
        # This should only contain 5 as the agents should be part of 
        # the agency.agents member:
        self.assertEquals(len(objs), 5)
        
        # This is the default order in which the objects should be recovered:
        self.assertEquals(objs[0].name, 'director')
        self.assertEquals(objs[0].order, 0)
        self.assertEquals(objs[1].name, 'webadmin')
        self.assertEquals(objs[1].order, 1)
        self.assertEquals(objs[2].name, 'agency')
        self.assertEquals(objs[2].order, 2)
        self.assertEquals(objs[3].name, 'checkdir')
        self.assertEquals(objs[3].order, 3)
        self.assertEquals(objs[4].name, 'broker')
        self.assertEquals(objs[4].order, 4)
        
        # Check the agents are present:
        agents = objs[2].agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'bat')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'aardvark')
        self.assertEquals(agents[1].order, 1)
        
    
    def testObjectRecovery(self):
        """Test the parsing of the config recovering any webadmin modules mentioned.
        """
        test_config = """
        [director]
        msg_host = "127.0.0.1"
        msg_port = 61613
        msg_username = ''
        msg_password = ''
        msg_channel = 'evasion'
        disable_broker = no
        poll_time = 1
        webadmin = 'director.webadmin'

        [broker]
        host="localhost"
        port=61613
        webadmin = 'webadminbroker'
        
        [agency]
        #disabled = 'yes'
        webadmin = 'agency.webadmin'

            [aardvark]
            #disabled = 'yes'
            cat = swipe
            agent = myswipe
            webadmin = 'webadmindog'

            [bat]
            #disabled = 'yes'
            cat = swipe
            agent = myswipe
            webadmin = 'webadmincat'

        [webadmin]
        host="127.0.0.1"
        port=29837

        [checkdir]
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"
        webadmin = 'bob.webadmin'
        
        [somerandomsection]
        # This will become a catch all container object.
        bob = '1234'
        uptime = True

        """
        objs = director.config.recover_objects(test_config)
        
        # This should only contain 6 as the agents should be part of 
        # the agency.agents member:
        self.assertEquals(len(objs), 6)
        
        # This is the default order in which the objects should be recovered:
        self.assertEquals(objs[0].name, 'director')
        self.assertEquals(objs[0].order, 0)
        self.assertEquals(objs[1].name, 'broker')
        self.assertEquals(objs[1].order, 1)
        self.assertEquals(objs[2].name, 'agency')
        self.assertEquals(objs[2].order, 2)
        self.assertEquals(objs[3].name, 'webadmin')
        self.assertEquals(objs[3].order, 3)
        self.assertEquals(objs[4].name, 'checkdir')
        self.assertEquals(objs[4].order, 4)
        self.assertEquals(objs[5].name, 'somerandomsection')
        self.assertEquals(objs[5].order, 5)
        
        # Check the agents are present:
        agents = objs[2].agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'aardvark')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'bat')
        self.assertEquals(agents[1].order, 1)
    




