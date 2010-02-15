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

.. autofunction:: director.config.clear()

.. autofunction:: director.config.get_cfg()

.. autofunction:: director.config.set_cfg(the_config

.. autoclass:: director.config.Container
   :members:
   :undoc-members:

.. autofunction:: director.config.load(config)

"""
import pprint
import logging
import StringIO
import traceback
import configobj
import itertools
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
__config = None


class ConfigStore:
    """
    An instance of this is used to store the original raw config and the ConfigObj instance.

    The original config data is stored as the 'raw' member variable.

    The ConfigObj instance is stored as the 'cfg' member variable.
    
    """
    def __init__(self, raw, cfg):
        self.raw = raw
        self.cfg = cfg


def clear():
    """Remove the stored config, this is used mainly by unittesting.
    
    If get_cfg() is called now ConfigNotSetup will be raised.
    
    """
    global __config
    __config = None
    

def get_cfg():
    """Called to return a reference to the currenlty set up configuration.
    
    If no config has been set up, via a call to set_config, then
    ConfigNotSetup will be raised to indicate so.
    
    """
    if not __config:
        raise ConfigNotSetup("No configuration has been setup.")
    
    return __config


def set_cfg(raw):
    """Called to set up the configuration used for the project.
    
    :param raw: this is a string representing the raw
    configuration data read from the config file.
    
    """
    global __config
    fd = StringIO.StringIO(raw)
    cfg = ConfigObj(infile=fd)
    __config = ConfigStore(raw, cfg)
    

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

    """
    cfg = configobj.ConfigObj(StringIO.StringIO(config))

    class R(object):
        def __init__(self):
            self.returned = []
            self.agency = None
            self.agents = []
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
                if section == 'agency':
                    # store agency so we can add agents to it.
                    self.agency = container
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
        type = 'container'
        if isinstance(obj, Director) or isinstance(obj, Broker) or \
           isinstance(obj, Agency) or isinstance(obj, WebAdmin):
            type = obj.name
        elif isinstance(obj, Agent):
            type = 'agent'
        elif isinstance(obj, Controller):
            type = 'controller'
        return dict(
            name=obj.name,
            type=type,
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


    
def load(config):
    """Called to test and then load the controller configuration.
    
    config:
        This is a string representing the contents of the
        configuration file.
    
    check:
        If this is given the callback will be invoked and
        given the node and alias of the config object. The
        callback can then check if its unique. Its up to the
        user to determine what to do if they're not.
    
    returned:
        This returns a list of config containers loaded with
        the entries recovered from the device's section.
    
    """
    cfg = configobj.ConfigObj(StringIO.StringIO(config))
    processed = {}
    
    def recover(section, key):        
        # If the section does not have and 'agent' then it is not considered and ignored.
        if 'controller' not in section:
            #get_log().info("The config section '%s' does not appear to be an controller key. Ignoring." % key)
            return
    
        value = section[key]
        disabled = section.get('disabled','no')
        c = processed.get(section.name, Container())            
        
        if not c.name:
            c.name = section.name    
        
        if not c.config:
            c.config = section
                        
        elif key == 'controller' and disabled == 'no':
            def recover_agent():
                # default: nothing found.
                returned = None
                
                # Check I can at least import the stated module.
                try:
                    importmod = section[key]
                    fromlist = section[key].split('.')
                    # absolute imports only (level=0):
                    imported_agent = __import__(importmod, fromlist=fromlist, level=0)
                    
                except ImportError, e:
                     raise ImportError("The controller '%s' from section '%s' was not found! %s" % (
                         importmod,
                         section,
                         traceback.format_exc()
                     ))

                # Now see if it contains a Controller category all agent must have to load:
                if hasattr(imported_agent, 'Controller'):
                    returned = getattr(imported_agent, 'Controller')
                    returned = returned()
                    
                return returned

            value = recover_agent()
            if not value:
                raise ConfigError("I was unable to import '%s' from '%s'." % (item, current))

        # Only store if this section isn't disabled
        if  disabled == 'no':
            setattr(c, key, value)
            processed[section.name] = c
        
    # Process all the config sections creating config containers.
    cfg.walk(recover)
    
    # Verify we've got all the sections I require:
    def order_setup_and_check(c):
        c.check()
        return (c.order, c)

    returned = [order_setup_and_check(c) for c in processed.values()]
    returned.sort()
    
    return returned


