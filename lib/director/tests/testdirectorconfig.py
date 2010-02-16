import os
import sys
import os.path
import pprint
import unittest
import tempfile
import director


class DirectorConfigTC(unittest.TestCase):
    """Exercise the director configuration functionality
    """
    
    def cleanUp(self, top):
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                #print 'name:',name
                os.remove(os.path.join(root, name))
            for name in dirs:
                #print 'dir name:',name
                os.rmdir(os.path.join(root, name))


    def testAgentControllerImport(self):
        """Test I can import Agent or Controller classes using the import_module
        """
        p = tempfile.mkdtemp()
        sys.path.append(p)
        try:
            # Create an agent inside a package so I can then test 
            # the absolute import on which the system is based.
            #
            # mypackage.myagent
            #
            mypkg = os.path.join(p,'mypackage')
            os.mkdir(mypkg)
            
            f = os.path.join(mypkg, '__init__.py')
            fd = open(f, 'wb')
            fd.write("\n")
            fd.close()
            
            # Create an agent module that import_module should find and load.
            #
            f = os.path.join(mypkg, 'myagent.py')
            fd = open(f, 'wb')
            fd.write("""

class Agent(object):
    pass
        
            """)
            fd.close()
            
            # This shouldn't create any import exceptions: 
            class Obj:
                type = 'agent'
                agent = 'mypackage.myagent'
            director.config.import_module(Obj.type, Obj())
            
            # Try this from configuration file:
            test_config = """
            [director]

            [agency]
            # I don't really need this here as its enabled by default
            disabled = 'no'
            
            [fancyagent]
            cat = 'misc'
            agent = 'mypackage.myagent'
            
            """
            objs = director.config.recover_objects(test_config)
            
            agents = director.config.load_agents(objs)

            self.assertEquals(len(agents), 1)
            m = __import__('mypackage.myagent', fromlist=['mypackage',])
            self.assertEquals(isinstance(agents[0], m.Agent), True, "Agent not recovered correctly!")
            
            controllers = director.config.load_controllers(objs)
            self.assertEquals(len(controllers), 0)
            
            
            # Create an controller module that import_module should find and load.
            #
            f = os.path.join(mypkg, 'mycontroller.py')
            fd = open(f, 'wb')
            fd.write("""

class Controller(object):
    pass
        
            """)
            fd.close()
            
            # This shouldn't create any import exceptions: 
            class Obj:
                type = 'controller'
                controller = 'mypackage.mycontroller'
            director.config.import_module(Obj.type, Obj())
            
            # Try this from configuration file:
            test_config = """
            [director]
            
            [supercontroller]
            controller = 'mypackage.mycontroller'
            
            """
            objs = director.config.recover_objects(test_config)
            agents = director.config.load_agents(objs)
            
            self.assertEquals(len(agents), 0)
            
            controllers = director.config.load_controllers(objs)
            self.assertEquals(len(controllers), 1)
            m = __import__('mypackage.mycontroller', fromlist=['mypackage',])
            self.assertEquals(isinstance(controllers[0], m.Controller), True, "Controller not recovered correctly!")
            
        finally:
            self.cleanUp(p)


    def testdirectorConfigByNameRecovery(self):
        """Test that I can get named config objects from the global configuration.
        """
        test_config = """
        [director]
        disabled = 'no'
        
        [broker]
        disabled = 'no'
        
        [agency]
        disabled = 'no'

            [aardvark]
            order = 1
            cat = swipe
            agent = myswipe

            [bat]
            order = 0
            cat = swipe
            agent = myswipe
            
        """
        director.config.clear()
        director.config.set_cfg(test_config)
        c = director.config.get_cfg()
        
        self.assertEquals(c.obj.director is None, False)
        self.assertEquals(c.obj.broker is None, False)
        self.assertEquals(c.obj.agency is None, False)
        self.assertEquals(c.obj.webadmin is None, True)
        
        # This is the default order in which the objects should be recovered:
        self.assertEquals(c.obj.director.name, 'director')
        self.assertEquals(c.obj.director.order, 0)
        
        # Check the agents are present:
        agents = c.obj.agency.agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'bat')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'aardvark')
        self.assertEquals(agents[1].order, 1)


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

        
    def testConfigErrors(self):
        """Test the bad configuration handling
        """
        # No director section
        test_config = ""
        director.config.clear()
        self.assertRaises(director.config.ConfigError, director.config.set_cfg, test_config)

        # Two+ director sections:
        test_config = """
        [director]
        
        [director]
        """
        director.config.clear()
        self.assertRaises(director.config.ConfigError, director.config.set_cfg, test_config)

        # Two+ broker sections:
        test_config = """
        [director]
        
        [broker]
        
        [broker]
        """
        director.config.clear()
        self.assertRaises(director.config.ConfigError, director.config.set_cfg, test_config)

        # Two+ agency sections:
        test_config = """
        [director]

        [agency]
        
        [agency]
        
        """
        director.config.clear()
        self.assertRaises(director.config.ConfigError, director.config.set_cfg, test_config)

        # Two+ webadmin sections:
        test_config = """
        [director]

        [webadmin]
        
        [webadmin]
        
        """
        director.config.clear()
        self.assertRaises(director.config.ConfigError, director.config.set_cfg, test_config)


    def testdirectorConfig(self):
        """Test the configuration set and machinery
        """
        test_config = """
        [director]
        disabled = 'no'
        
        [broker]
        disabled = 'no'
        
        [agency]
        disabled = 'no'

            [aardvark]
            order = 1
            cat = swipe
            agent = myswipe

            [bat]
            order = 0
            cat = swipe
            agent = myswipe
            
        """
        
        # Reset and Check that no setup done is caught:
        director.config.clear()
        
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        director.config.set_cfg(test_config)
        
        c = director.config.get_cfg()
        
        # This should only contain 5 as the agents should be part of 
        # the agency.agents member:
        self.assertEquals(len(c.cfg), 3)
        
        # This is the default order in which the objects should be recovered:
        self.assertEquals(c.cfg[0].name, 'director')
        self.assertEquals(c.cfg[0].order, 0)
        self.assertEquals(c.cfg[1].name, 'broker')
        self.assertEquals(c.cfg[1].order, 1)
        self.assertEquals(c.cfg[2].name, 'agency')
        self.assertEquals(c.cfg[2].order, 2)
        
        # Check the agents are present:
        agents = c.cfg[2].agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'bat')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'aardvark')
        self.assertEquals(agents[1].order, 1)


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
    




