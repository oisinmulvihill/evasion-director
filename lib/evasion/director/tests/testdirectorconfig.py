import os
import sys
import os.path
import pprint
import unittest
import tempfile

from evasion import director
from evasion.director import config 


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
            config.import_module(Obj.type, Obj())
            
            # Try this from configuration file:
            test_config = """
            [director]
            
            [agency]
            order = 1
            disabled = 'no'
            
            [fancyagent]
            order = 2
            cat = 'misc'
            agent = 'mypackage.myagent'
            
            [willnotshowup]
            disabled = 'yes'
            order = 3
            cat = 'misc'
            agent = 'mypackage.myagent'
            bob = '1234'
            port = 59876
            
            """
            config.set_cfg(test_config)
            c = config.get_cfg()
            
            objs = config.load_agents(c.cfg)

            # The agency will be in position 1 (order 1). There should be
            # two agents present, even though the second one is disabled.
            self.assertEquals(len(objs[1].agents), 2)
            
            # Check the config section is stored as part of the config 
            # attribute:
            a = objs[1].agents[1]
            self.assertEquals(a.config['disabled'], 'yes')
            self.assertEquals(a.config['order'], '3')
            self.assertEquals(a.config['cat'], 'misc')
            self.assertEquals(a.config['agent'], 'mypackage.myagent')
            self.assertEquals(a.config['bob'], '1234')
            self.assertEquals(a.config['port'], '59876')
            
            m = __import__('mypackage.myagent', fromlist=['mypackage',])
            self.assertEquals(isinstance(objs[1].agents[0].mod, m.Agent), True, "Agent not recovered correctly!")
            
            # The disabled agent should not be imported.
            m = __import__('mypackage.myagent', fromlist=['mypackage',])
            self.assertEquals(objs[1].agents[1].mod, None, "Agent was imported when it should not have been!")
            
            # try updating the config_objs and recheck that the change has been stored.
            config.update_objs(objs)
            c = config.get_cfg()
            self.assertEquals(isinstance(objs[1].agents[0].mod, m.Agent), True, "Agent not stored+updated correctly!")
            self.assertEquals(isinstance(c.agency.agents[0].mod, m.Agent), True, "Agent not stored+updated correctly!")
            
            
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
            config.import_module(Obj.type, Obj())
            
            # Try this from configuration file:
            test_config = """
            [director]

            [agency]
            order = 1
            disabled = 'yes'
            
            [supercontroller]
            order = 2
            controller = 'mypackage.mycontroller'
            
            """
            config.set_cfg(test_config)
            c = config.get_cfg()
            
            self.assertEquals(len(c.cfg), 3)
            objs = config.load_controllers(c.cfg)
            
            msg = """
            Inital config != result from load_controllers
            
            c.objs:            
            %s
            
            loaded objs:
            %s
            
            """ % (c.cfg, objs)
            
            self.assertEquals(len(objs), 3, msg)
            
            m = __import__('mypackage.mycontroller', fromlist=['mypackage',])
            
            # The supercontroller will be in this position:
            self.assertEquals(isinstance(objs[2].mod, m.Controller), True, "Controller not recovered correctly!")

            # try updating the config_objs and recheck that the change has been stored.
            config.update_objs(objs)
            c = config.get_cfg()
            self.assertEquals(len(objs), 3)
            m = __import__('mypackage.mycontroller', fromlist=['mypackage',])
            self.assertEquals(isinstance(objs[2].mod, m.Controller), True, "Controller not recovered correctly!")
            
            
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
        config.clear()
        config.set_cfg(test_config)
        c = config.get_cfg()
        
        self.assertEquals(c.director is None, False)
        self.assertEquals(c.broker is None, False)
        self.assertEquals(c.agency is None, False)
        self.assertEquals(c.webadmin is None, True)
        
        # This is the default order in which the objects should be recovered:
        self.assertEquals(c.director.name, 'director')
        self.assertEquals(c.director.order, 0)
        
        # Check the agents are present:
        agents = c.agency.agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'bat')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'aardvark')
        self.assertEquals(agents[1].order, 1)

        
    def testConfigErrors(self):
        """Test the bad configuration handling
        """
        # No director section
        test_config = ""
        config.clear()
        self.assertRaises(config.ConfigError, config.set_cfg, test_config)

        # Two+ director sections:
        test_config = """
        [director]
        
        [director]
        """
        config.clear()
        self.assertRaises(config.ConfigError, config.set_cfg, test_config)

        # Two+ broker sections:
        test_config = """
        [director]
        
        [broker]
        
        [broker]
        """
        config.clear()
        self.assertRaises(config.ConfigError, config.set_cfg, test_config)

        # Two+ agency sections:
        test_config = """
        [director]

        [agency]
        
        [agency]
        
        """
        config.clear()
        self.assertRaises(config.ConfigError, config.set_cfg, test_config)

        # Two+ webadmin sections:
        test_config = """
        [director]

        [webadmin]
        
        [webadmin]
        
        """
        config.clear()
        self.assertRaises(config.ConfigError, config.set_cfg, test_config)


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
        config.clear()
        
        self.assertRaises(config.ConfigNotSetup, config.get_cfg)

        # Check we don't get and problems with files...
        config.set_cfg(test_config)
        
        c = config.get_cfg()
        
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
        objs = config.recover_objects(test_config)
        
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

        [broker]
        host="localhost"
        port=61613
        
        [agency]
        #disabled = 'yes'

            [aardvark]
            #disabled = 'yes'
            cat = swipe
            agent = myswipe

            [bat]
            #disabled = 'yes'
            cat = swipe
            agent = myswipe

        [webadmin]
        host="127.0.0.1"
        port=29837

        [checkdir]
        controller = 'director.controllers.commandline'
        command = "ls"
        workingdir = "/tmp"
        
        [somerandomsection]
        # This will be ignored entirely and will not appear in the recovered objects.
        bob = '1234'
        uptime = True

        """
        objs = config.recover_objects(test_config)
        
        # This should only contain 6 as the agents should be part of 
        # the agency.agents member:
        self.assertEquals(len(objs), 5)
        
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
        
        # Check the agents are present:
        agents = objs[2].agents
        self.assertEquals(len(agents), 2)
        
        # Check the default ordering of the recovered agents:
        self.assertEquals(agents[0].name, 'aardvark')
        self.assertEquals(agents[0].order, 0)
        self.assertEquals(agents[1].name, 'bat')
        self.assertEquals(agents[1].order, 1)
    




