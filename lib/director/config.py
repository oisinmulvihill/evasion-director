"""
:mod:`config` -- This supervises then agents under its control.
=================================================================

.. module:: config
   :platform: Unix, MacOSX, Windows
   :synopsis: This supervises then agents under its control.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module provides the director configuration parsing and handling. 

.. exception:: director.config.ConfigInvalid

.. exception:: director.config.ConfigNotSetup

.. exception:: director.config.ConfigError

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
from configobj import ConfigObj


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


__config = None


def clear():
    """Remove the stored config, this is used mainly by unittesting.
    
    If get_cfg() is called now ConfigNotSetup will be raised.
    
    """
    global __config
    __config = None
    

def get_cfg():
    """Called to return a reference to the currenlty set up configuration.
    
    If no config has been set up, via a call to set_config,
    then ConfigNotSetup will be raised to indicate so.

    Note: the configuration only returns the configobj
    information from the 'director' section and not
    any others that could be present in the config.
    
    """
    if not __config:
        raise ConfigNotSetup, "No configuration has been setup."        
    return __config['director']


def set_cfg(the_config):
    """Called to set up the configuration used for the project.
    
    the_config:
    
    """
    global __config
    cfg = ConfigObj(infile=the_config)
    try:
        cfg['director']
    except KeyError,e:
        raise ConfigInvalid, "No [director] section was found in the given configuration (case is important)."
        
    #print "cfg: ", cfg
    __config = cfg
    

c = property(get_cfg, set_cfg)


class Container(object):
    """This represents a configuration sections as recoverd from the configuration.    
    
    A config section can have the following options::
    
        [name]        
        # Order in which to start programs (must be unique)
        order = 1

        # The python path to agent to import e.g.
        controller = 'director.controllers.program'
                        
        # OPTIONAL: disable the start/stop of the controller. It will
        # still be loaded and created.
        disabled = 'yes' | 'no'

        # Other customer configuration can also be put in each
        # section. I just look for the above alone and ignore
        # anything else.
    
    """
    reserved = ()
    def __init__(self):
        self.name = None
        self.order = None
        self.controller = None
        self.disabled = "no"
        self.reserved = ('controller', 'order', 'name')
        self.config = None
        self.controller = None
    
    def check(self):
        """Called to check that all the reserved fields have been provided.
        
        If one or more aren't provided then ConfigError
        will be raised to indicate so.
        
        """
        for i in self.reserved:
            if not getattr(self, i, None):
                raise ConfigError("The member '%s' must be provided in the configuration." % i)        
    
    def __str__(self):
        """Print out who were representing and some unique identifier."""
        #print "self:", self.__dict__
        return "<Controller: name %s, order %s>" % (self.name, self.order)

    
    def __repr__(self):
        """This is a string the represents us, can be used as a dict key."""
        return self.__str__()


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
            get_log().info("The config section '%s' does not appear to be an controller key. Ignoring." % key)
            return
    
        value = section[key]
        c = processed.get(section.name, Container())            
        
        if not c.name:
            c.name = section.name    
        
        if not c.config:
            c.config = section
                        
        elif key == 'controller':
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

                # Now see if it contains a Agent category all agent must have to load:
                if hasattr(imported_agent, 'Controller'):
                    returned = getattr(imported_agent, 'Controller')
                    
                return returned

            value = recover_agent()
            if not value:
                raise ConfigError("I was unable to import '%s' from '%s'." % (item, current))
                        
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
    
    
    
    
    


