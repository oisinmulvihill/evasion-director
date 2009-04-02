"""
"""
from configobj import ConfigObj


class ConfigInvalid(Exception):
    """Raised when the config doesn't have the director section or
    other things we require.
    """

class ConfigNotSetup(Exception):
    """Raised when set_cfg hasn't been called to set up the configuration.
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
    
