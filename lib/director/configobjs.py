"""
:mod:`configobjs` -- Provides objects that represent config sections
===================================================================

.. module:: config
   :platform: Unix, MacOSX, Windows
   :synopsis: Provide objects that represent config sections from the director.cfg
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module provides the director configuration parsing and handling. 

.. autoexception:: director.configobjs.ConfigError

.. autoclass:: director.configobjs.Director
   :members:

.. autoclass:: director.configobjs.Broker
   :members:

.. autoclass:: director.configobjs.WebAdmin
   :members:

.. autoclass:: director.configobjs.Controller
   :members:

.. autoclass:: director.configobjs.Agent
   :members:

.. autoclass:: director.configobjs.Container
   :members:

"""
import logging

all = [
    'SectionError', 'Director', 'Broker', 'WebAdmin', 
    'Controller', 'Agency', 'Agent', 'Container',
]


class SectionError(Exception):
    """This is raised for problems with loading and using the configuration.
    """

    
class Base(object):
    """This is the base for all objects converted to from configuration sections.
    """
    def __init__(self):
        """
        Set up the base members name, order, disabled = 'no', config
        """
        self.required = []
        self.name = None
        self.order = None
        self.disabled = "no"
        # This is a dict of the config section.
        self.config = None
        self.webadmin = ''
        # This is the loaded module as recovered by import_module
        # via a call to load_agents / load_controllers.
        self.mod = None


    def __str__(self):
        """Print out who were representing and some unique identifier."""
        #print "self:", self.__dict__
        return "<%s: order %s>" % (self.name, self.order)

    
    def __repr__(self):
        """This is a string the represents us, can be used as a dict key."""
        return self.__str__()


    def validate(self):
        """Called to check that all the required fields have been provided.
        
        If one or more aren't provided then SectionError
        will be raised to indicate so.
        
        """
        for i in self.required:
            if i and not getattr(self, i, None):
                raise SectionError("'%s' The member '%s' must be provided in the configuration." % (str(self), i))
    

class Director(Base):
    """This represents a director section as recovered from the 
    configuration section.    
    
    A config section can have the following options::
    
        [director]
        # The broker connection details. Required if disable_broker = 'no' (default):
        msg_host = "127.0.0.1"
        msg_port = 61613
        msg_username = ''
        msg_password = ''
        msg_channel = 'evasion'

        # (OPTIONAL): Set this to 'yes' if you wish to stop the director connecting to the broker.
        disable_broker = 'no'

        # (OPTIONAL) Prevent director busy waiting. This just limits the time between maintenances checks.
        # This is in seconds or fractions of seconds, the default being 0.1s.
        poll_time = 1

        # (OPTIONAL): To disable the special proxy dispatch set this to 'yes'
        noproxydispatch = 'no'

        # (OPTIONAL): Web app local reply dispatch XML-RPC service i.e. http://localhost:<this port>/RPC2.
        proxy_dispatch_port = 1901

        # (OPTIONAL): This is the option web interface to be used if webadmin is used.
        webadmin = 'director.webadmin'

        # Notes: 
        #
        # The director has an implicit order of 0
        # order = 0
        #
        # Other customer configuration can also be put in each
        # section. I just look for the above alone and ignore
        # anything else.

    """
    type = 'director'
    
    def __init__(self):
        Base.__init__(self)
        self.name = self.type
        self.order = 0
        self.poll_time = float(1.0)
        self.msg_host = '127.0.0.1'
        self.msg_port = 61613
        self.msg_username = ''
        self.msg_password = ''
        self.msg_channel = 'evasion'
        self.disable_broker = 'no'
        self.noproxydispatch = 'no'
        self.proxy_dispatch_port = 1901
        self.webadmin = '' #'director.webadmin'
        
        # Fake the director's mod so it can be used like a controller.
        #
        class F:
            """Based on director.controllers.base:Base but 
            there is no point importing it just for this.
            """
            def setUp(self, config): pass
            def start(self): pass
            def isStarted(self): return True
            def stop(self): return True
            def isStopped(self): return True
            def tearDown(self): pass
        self.mod = F()


    def __str__(self):
        return "<Director: order:%s>" % (self.order)


class Broker(Base):
    """This represents a broker section as recovered from the 
    configuration.    
    
    A config section can have the following options::
    
        [broker]
        # OPTIONAL: This is the order in which it will be started.
        # The default is 1 to come after the directors implicit 0.
        order = 1
        
        # OPTIONAL: The broker is using the command line controller 
        # for the moment. The controller/command/workingdir are args
        # for the commandline controller. In future the broker may
        # run as a thread under the director.
        #
        controller = 'director.controllers.commandline'
        command = "morbidsvr -p 61613 -i 127.0.0.1"
        workingdir = ""
        
        # OPTIONAL: disable the start/stop of the controller. It will
        # still be loaded and created.
        disabled = 'yes' | 'no'

    """
    type = 'broker'
    
    def __init__(self):
        Base.__init__(self)
        self.name = self.type
        self.order = 1
        self.disabled = 'no'
        self.controller = 'director.controllers.commandline'
        self.command = "morbidsvr -p 61613 -i 127.0.0.1"
        self.workingdir = ""


    def __str__(self):
        return "<Broker: order:%s disabled:%s>" % (self.order, self.disabled)


class Agency(Base):
    """This represents the Agency configuration as recoverd 
    from the configuration.    
    
    A config section can have the following options::
    
        [agency]
        order = 2
        
        # (OPTIONAL): This is the option web interface to be used if 
        # webadmin is used.
        #
        webadmin = 'agency.webadmin'
        
        # OPTIONAL: disable the setup/tearDown/start/stop of the
        # agent. It will still be loaded and created.
        disabled = 'yes' | 'no'
        
    Note: the 'agents' member will contain a list agent instances
    recovered.
    
    """
    type = 'agency'
    
    def __init__(self):
        Base.__init__(self)
        self.name = self.type
        self.order = 2
        self.webadmin = '' #'agency.webadmin'
        self.disabled = 'no'
        self.controller = 'director.controllers.agencyctrl'
        self.agents = []

    def __str__(self):
        return "<Agency: order:%s disabled:%s>" % (self.order, self.disabled)


class Agent(Base):
    """This represents an agent configuration section as recoverd 
    from the agent configuration.    
    
    A config section can have the following options::
    
        [name]
        # The python path to agent to import e.g.
        agent = 'agency.testing.fake'
        
        # A category from agency.AGENT_CATEGORIES
        cat = 'general'
        
        # OPTIONAL: the order in which the agent will be 
        # started. By default it will be given an order 
        # based on when it was recoverd.
        # order = 0+
        
        # OPTIONAL: a unique number which can be used instead of name
        # to refer to this agent.
        alias = 1
        
        # OPTIONAL: disable the setup/tearDown/start/stop of the
        # agent. It will still be loaded and created.
        disabled = 'yes' | 'no'
    
    """
    type = 'agent'
    
    def __init__(self):
        Base.__init__(self)
        self.agent = None
        self.cat = None
        self.alias = None
        self.node = None
        # This will be set if its not provided:
        self.order = None 
        # alias is no longer required.
        self.required = ['name','agent', 'cat']


    def __str__(self):
        return "<Agent: name:%s agent order:%s disabled:%s>" % (
            self.name, 
            self.order, 
            self.disabled
        )


class WebAdmin(Base):
    """This represents a broker section as recovered from the 
    configuration.    
    
    A config section can have the following options::
    
        [webadmin]
        # The interface to bind to (default is localhost):
        host = '127.0.0.1'
        
        # The TCP port to open on (default is 29875):
        port = 29875
        
        # OPTIONAL: This is the order in which it will be started.
        order = 3
        
        # OPTIONAL: The webadmin is using the command line controller 
        # for the moment. The controller/command/workingdir are args
        # for the commandline controller. In future the webadmin may
        # run as a thread under the director.
        #
        controller = 'director.controllers.commandline'
        command = "runwebadmin --config development.ini"
        workingdir = ""
        
        # OPTIONAL: disable the start/stop of the controller. It will
        # still be loaded and created.
        disabled = 'yes' | 'no'

    """
    type = 'webadmin'
    
    def __init__(self):
        Base.__init__(self)
        self.name = self.type
        self.order = 4
        self.disabled = 'no'
        self.host = '127.0.0.1'
        self.port = 29875
        
        # Use the default root site admin:
        self.webadmin = "webadmin"
        
        # noop for the moment:
        self.controller = 'director.controllers.base'
        self.command = "runwebadmin --config development.ini"
        self.workingdir = ""


    def __str__(self):
        return "<WebAdmin: order:%s disabled:%s>" % (self.order, self.disabled)


class Controller(Base):
    """This represents a controller section as recovered from the 
    configuration section.    
    
    A config section can have the following options::
    
        [name]        
        # Order in which to start programs (must be unique)
        # order = 10+

        # The python path to agent to import e.g.
        controller = 'director.controllers.program'
                        
        # OPTIONAL: disable the start/stop of the controller. It will
        # still be loaded and created.
        disabled = 'yes' | 'no'

        # Other customer configuration can also be put in each
        # section. I just look for the above alone and ignore
        # anything else.
    
    """
    type = 'controller'
    
    def __init__(self):
        Base.__init__(self)
        self.required = ['name','order','controller']
        self.controller = None


    def __str__(self):
        return "<Controller: order:%s name:%s disabled:%s>" % (self.order, self.name, self.disabled)


class Container(Base):
    """This represents an abitrary (unknown) section recovered 
    from the configuration. The '[<section>]' will become the 
    name of the container.
    """
    type = 'container'
    
    def __init__(self):
        Base.__init__(self)

    
    def validate(self):
        """No validation is performed on arbitrary containers."""
        pass

    def __str__(self):
        return "<Container: %s>" % (self.name)

