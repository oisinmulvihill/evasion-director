"""
:mod:`config` -- This supervises then agents under its control.
=================================================================

.. module:: config
   :platform: Unix, MacOSX, Windows
   :synopsis: This supervises then agents under its control.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module provides the director configuration parsing and handling. 

.. autoexception:: director.config.ConfigInvalid

.. autoexception:: director.config.ConfigNotSetup

.. autoexception:: director.config.ConfigError

.. autoclass:: director.config.ConfigStore
   :members:

.. autofunction:: director.config.clear

.. autofunction:: director.config.get_cfg

.. autofunction:: director.config.set_cfg

.. autoclass:: director.config.Container
   :members:
   :undoc-members:

.. autofunction:: director.config.recover_objects

.. autofunction:: director.config.webadmin_modules

.. autofunction:: director.config.load_agents

.. autofunction:: director.config.load_controllers

"""
import copy
import pprint
import logging
import StringIO
import traceback
import configobj
import itertools
import threading
from configobj import ConfigObj


from configobjs import *


def get_log():
    return logging.getLogger('agency.config')


class ConfigInvalid(Exception):
    """Raised when the config doesn't have the director section or
    other things we require.
    """

class ConfigNotSetup(Exception):
    """Raised when set_cfg hasn't been called to set up the configuration.
    """

class ConfigError(Exception):
    """This is raised for problems with loading and using the configuration.
    """


# Private: represents the current ConfigStore instance
# holding the config and configobj instance.
#
__configLock = threading.Lock()
__config = None


class ConfigStore:
    """
    An instance of this is used to store the original raw config and the ConfigObj instance.

    The original config data is stored as the 'raw' member variable.

    The ConfigObj instance is stored as the 'cfg' member variable.
    
    The director, broker, agency and webadmin are members which will
    not be None. These will be set up if the are present in the cfg
    configuration objects.
    
    """
    def __init__(self, raw, cfg):
        self.raw = raw
        self.cfg = cfg
        self.director = None
        self.broker = None
        self.agency = None
        self.webadmin = None
        for i in cfg:
            if i.name == 'director':
                self.director = i
            if i.name == 'broker':
                self.broker = i
            if i.name == 'agency':
                self.agency = i
            if i.name == 'webadmin':
                self.webadmin = i


def clear():
    """Remove the stored config, this is used mainly by unittesting.
    
    If get_cfg() is called now ConfigNotSetup will be raised.
    
    """
    global __config
    __configLock.acquire()
    __config = None
    __configLock.release()
    

def get_cfg():
    """Called to return a reference to the currenlty set up configuration.
    
    If no config has been set up, via a call to set_config, then
    ConfigNotSetup will be raised to indicate so.
    
    """
    if not __config:
        raise ConfigNotSetup("No configuration has been setup.")
    __configLock.acquire()
    try:
        rc =  copy.deepcopy(__config)
    finally:
        __configLock.release()
        
    return rc
    

def update_objs(objs):
    """Called to updated the current cached store of config objs.

    :param objs: this is a list of configuration object
    as returned by a call from recover_objects.
    
    This function will typically be done after a load_agents 
    or load_controllers.
    
    If no config has been set up, via a call to set_config, then
    ConfigNotSetup will be raised to indicate so.
    
    """
    global __config
    if not __config:
        raise ConfigNotSetup("No configuration has been setup.")
    __configLock.acquire()
    try:
        __config = ConfigStore(__config.raw, objs)
    finally:
        __configLock.release()


def set_cfg(raw):
    """Called to set up the configuration used for the project.
    
    :param raw: this is a string representing the raw
    configuration data read from the config file.
    
    """
    global __config
    
    # Recover the objects and store them:
    objs = recover_objects(raw)
    
    __configLock.acquire()
    try:
        __config = ConfigStore(raw, objs)
    finally:
        __configLock.release()
    

MAPPED_SECTIONS = dict(
    # (Default order, class to store details in) 
    director = (0, Director),
    broker = (1, Broker),
    agency = (2, Agency),
    webadmin = (3, WebAdmin),
)

def recover_objects(config):
    """
    Called to walk through the configuration and convert the
    sections into their equivalent configobjs.
    
    This function does not attempt to import any modules, it
    simply creates the main containers. The load_modules() 
    function does this on this functions output.
    
    The webadmin_modules() function uses the output of this 
    function to recover its information from.
    
    config:
        This is a string representing the contents of the
        configuration file.
    
    returned:
        A list of configuration objects which with the default 
        ordering will usually contain
        
        returned = [
            Director instance,
            Broker instance,
            Agency instance,
            WebAdmin instance,
            :
            other controllers in there order
        ]

        The Agency will contain the list of agents as part of
        its agents member and these will be ordered by defaults
        or by the order attribute if it was used.

    ConfigError will be raised if the configuration contains two
    sections with the same name.

    If the configuration does not contain the [director] section
    the ConfigError will be raised.
    
    """
    try:
        cfg = configobj.ConfigObj(StringIO.StringIO(config))
        
    except configobj.DuplicateError, e:
        raise ConfigError('Error in director configuraion - %s' % e)

    class R(object):
        def __init__(self):
            self.returned = []
            self.agency = None
            self.agents = []
            self.director = None
            self.broker = None
            self.webadmin = None
            self.agentCount = itertools.count(0)
            # Start at 4, 0-3 are reserved by default
            # for director,broker,agency&webadmin:
            self.sectionCounter = itertools.count(4)
    
        def setup(self, c, s):
            # Store all items we recovered
            for key, value in s.items():
                #print "key, value: ", key, value
                if key == 'order':
                    # Make these numbers and not strings.
                    value = int(value)
                setattr(c, key, value)

        def recover(self, section):
            """Convert to configobjs"""
            rsection = cfg[section]
            if section in MAPPED_SECTIONS:
                default_order, container = MAPPED_SECTIONS[section]
                container = container()
                if 'name' in rsection:
                    # remove this if its present in favour of hardcoded.
                    rsection.pop('name')
                if 'order' not in rsection:
                    container.order = default_order
                if section == 'director':
                    self.director = container
                if section == 'broker':
                    self.broker = container
                if section == 'agency':
                    self.agency = container
                if section == 'webadmin':
                    self.webadmin = container
                self.setup(container, rsection)
                
            elif 'agent' in rsection:
                container = Agent()
                self.setup(container, rsection)
                container.name = section
                if not container.order:
                    container.order = self.agentCount.next()
                self.agents.append([container.order, container])
                
                # Note: agents will be discarded if no agency is 
                # present in the configuration.
                return
                
            elif 'controller' in rsection:
                container = Controller()
                self.setup(container, rsection)
                container.name = section
                if 'order' not in rsection:
                    container.order = self.sectionCounter.next()
            
            else:
                container = Container()
                self.setup(container, rsection)
                container.name = section
                if 'order' not in rsection:
                    container.order = self.sectionCounter.next()
            
            self.returned.append([container.order, container])

    r = R()
    [r.recover(section) for section in cfg]

    # Check there is at least a director section
    if not r.director:
        raise ConfigError("The configuration contains no [director] section!")
    
    # Add any recovered agents to the agency 'agents' member:
    if r.agency:
        # sort the agents first:
        r.agents.sort()
        # strip the order and return just the agents in that order:
        r.agency.agents = [a for o,a in r.agents]
    
    # Sort all except agents which are part of the agency:
    r.returned.sort()
    
    # Check each container has the required parts:
    def v(c):
        c.validate()
        return c
        
    # Strip the order and return just the objects in that 
    # order, after validating them:
    #
    returned = [v(c) for order, c in r.returned]
        
    return returned


def webadmin_modules(config_objs):
    """
    Called to walk through the configuration objects and
    recover a list of webadmin modules from any object with
    it.
    
    config_objs:
        This is a list as returned by recover_objects()
    
    returned:
        A list of module names or and empty list if non were found.
        
        Format = [{
                'webadmin' : '...', # contents of webadmin field.
                'name' : '...', 
                'type' : 'director' | 'broker' | 'agency' | 'webadmin' |
                         'agent' | 'controller' | 'container'  
            },
            :
            etc
        ]

    """
    returned = []

    def setup(obj):
        return dict(
            name=obj.name,
            type=obj.type,
            webadmin=obj.webadmin,
        )
    
    def recover(obj):
        disabled = getattr(obj, 'disabled', 'no')
        webadmin = getattr(obj, 'webadmin', '')
        webadmin = webadmin.strip()
        
        if disabled == 'no' and webadmin:
            returned.append(setup(obj))
            if obj.name == 'agency':
                # put the agents after agency hq
                [recover(o) for o in obj.agents]

    [recover(o) for o in config_objs]

    return returned


def import_module(import_type, obj):
    """
    Called to import a module as recovered from the agent
    or controller attribute.
    
    :param import_type: 'agent' or 'controller'
    
    The agent or controller attributes must contain the 
    absolute import path. I.e <mypackage>.<mymodule>
    
    The import must contain a class called Agent or
    Controller.
    
    """
    # default: nothing found.
    returned = None
    
    if import_type == 'agent':
        import_string = obj.agent
        import_class = 'Agent'
    else:
        import_string = obj.controller
        import_class = 'Controller'
    
    # Check I can at least import the stated module.
    try:
        importmod = import_string
        fromlist = import_string.split('.')
        # absolute imports only (level=0):
        #get_log().debug("import_module: import<%s> fromlist<%s>" % (importmod, fromlist))
        imported_agent = __import__(importmod, fromlist=fromlist, level=0)
        
    except ImportError, e:
         raise ImportError("The controller '%s' from '%s' could not be imported! %s" % (
             importmod,
             obj,
             traceback.format_exc()
         ))

    # Now see if it contains a Controller category all agent must have to load:
    if hasattr(imported_agent, import_class):
        returned = getattr(imported_agent, import_class)
        returned = returned()
        
    return returned


def load_agents(config_objs):
    """Called to test and then load the agents from the configuration.
    
    If the [agency] is disabled then no agents will be 
    present to load. The agency is enabled by default,
    so any agents entries will be present in the agency's
    agents member.
    
    config_objs:
        This is a list as returned by recover_objects()
    
    returned:
        This returns a list of config containers loaded with
        the entries recovered from the device's section.
    
    """
    for obj in config_objs:
        if obj.disabled == 'no' and obj.type == 'agency':
            for a in obj.agents:
                if a.disabled == 'no':
                    a.mod = import_module(a.type, a)

    return config_objs

    
def load_controllers(config_objs):
    """Called to test and then load the controllers from the configuration.
    
    config_objs:
        This is a list as returned by recover_objects()
    
    Note: the broker, agency and webadmin are also considered 
    controllers in addition to the explicit controllers.
    
    returned:
        This returns the given config_objs with the mod field
        of each controller entry updated with the imported 
        module.
    
    """
    skip = ['director', 'container']
    
    def doimp(obj):
        if obj.disabled == 'no' and obj.type not in skip:
            obj.mod = import_module(obj.type, obj)
            
    [doimp(obj) for obj in config_objs]
    
    return config_objs

