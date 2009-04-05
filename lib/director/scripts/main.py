"""
Oisin Mulvihill
2007-05-18

"""
import os
import sys
import os.path
import logging
import logging.config
from configobj import ConfigObj
from optparse import OptionParser


def get_log():
    return logging.getLogger("director.managermain")



DEFAULT_CONFIG_NAME = "director.cfg"
DEFAULT_LOGCONFIG_NAME = "director-log.cfg"
DEFAULT_SERVICESTATION_NAME = "servicestation.cfg"


def create_config(cfg_dict):
    """Create the default director.ini in the current directory based
    on a the template stored in director.templatecfg

    cfg_dict contains:

    root_path:
       This root used in the template to where python+director is
       installed, from the installer.

    python_exe:
       This is the absolute path and python.exe to use for calls in
       the configuration.

    log_dir:
       This is the directory to write logs to. It must be an absolute
       path as this will be added to the director-log.ini file.

    director_log_cfg:
       What and where to find the director logging configuration.

    da_config:
       The file and path for deviceaccess.ini

    manager_config:
       The file and path for manager.ini
       
    disable_xul:    'yes' | 'no'
    disable_app:    'yes' | 'no'
    disable_broker: 'yes' | 'no'
    disable_device: 'yes' | 'no'
    
    """
    import director
    import director.templatecfg
    from pkg_resources import resource_string
    from mako.template import Template

    print("Creating initial configuration.")

    # Fill in the template information with XUL Browser path:
    import viewpoint
    cfg_dict['viewpoint_path'] = os.path.abspath(viewpoint.__path__[0])

    def writeout(filename, data):
        # Ok, write the result out to disk:
        fd = open(filename, 'w')
        fd.write(data)
        fd.close()

    # Fill in the template information with XUL Browser path:
    cfg_data = resource_string(director.templatecfg.__name__, 'director.cfg.mako')
    data = Template(cfg_data).render(**cfg_dict)
    writeout(DEFAULT_CONFIG_NAME, data)

    logcfg_data = resource_string(director.templatecfg.__name__, 'director-log.cfg.mako')
    cfg_dict['log_dir'] = cfg_dict['log_dir'].replace("\\","/")
    
    data = Template(logcfg_data).render(**cfg_dict)
    writeout(DEFAULT_LOGCONFIG_NAME, data)

    cfg_data = resource_string(director.templatecfg.__name__, 'servicestation.cfg.mako')
    data = Template(cfg_data).render(**cfg_dict)
    writeout(DEFAULT_SERVICESTATION_NAME, data)

    print("Success, '%s', '%s' and '%s' created ok." % (DEFAULT_CONFIG_NAME, DEFAULT_LOGCONFIG_NAME, DEFAULT_SERVICESTATION_NAME))


def main():
    """Set up the LANG ID prior to importing the device layer code.
    """
    parser = OptionParser()
    
    parser.add_option("--logconfig", action="store", dest="logconfig_filename", default="log.ini",
                      help="This is the logging config file.")
    
    parser.add_option("--create", action="store_true", dest="create_config", default=False,
                      help=(
                         "Create a configuration file from the internal template. The file"
                         "%s' will be created in the current directory." % DEFAULT_CONFIG_NAME
                      ))
                      
    parser.add_option("--installhome", action="store", dest="install_home",
                      default=r"c:\\evasion\\director",
                      help="Used by the install and --create to setup template root path.")
                      
    parser.add_option("--pythonexe", action="store", dest="python_exe",
                      default=r"python",
                      help="Used by the install and --create to setup '/the/path/to/python.exe'.")
                      
    parser.add_option("--logdir", action="store", dest="log_dir", default=r"c:\\evasion\\logs",
                      help="Used by the install and --create to setup the log dir.")
                      
    parser.add_option("--directorlogcfg", action="store", dest="director_log_cfg",
                      default=r"c:\\evasion\\cfg\\director-log.ini",
                      help="Used by the install and --create to setup the log dir.")
                      
    parser.add_option("--disableapp", action="store", dest="disable_app",
                      default="yes",
                      help="Used disable the web application.")
                      
    parser.add_option("--disablexul", action="store", dest="disable_xul",
                      default="yes",
                      help="Used disable the xul browser.")
                      
    parser.add_option("--disabledevice", action="store", dest="disable_device",
                      default="no",
                      help="Used disable the device manager.")
                      
    parser.add_option("--disablebroker", action="store", dest="disable_broker",
                      default="no",
                      help="Used disable the broker.")
                      
    parser.add_option("--dlconfig", action="store", dest="da_config",
                      default=r"c:\\evasion\\cfg\\director\\devices.cfg",
                      help="Used by the install and --create to setup where the devices.cfg is.")
                      
    parser.add_option("--dmconfig", action="store", dest="manager_config",
                      default=r"c:\\evasion\\cfg\\director\\manager.cfg",
                      help="Used by the install and --create to setup where the manager.cfg is.")

    parser.add_option("--config", action="store", dest="config_filename", default=DEFAULT_CONFIG_NAME,
                      help="This projects config file.")

    parser.add_option("--service_workingdir", action="store", dest="servicestation_workingdir", default="c:\\evasion\\director",
                      help="The directory that servcestation will run the director from.")                      

    (options, args) = parser.parse_args()

    log = logging.getLogger("")


    # Create the default app manager config:
    if options.create_config:
        cfg = dict(
            install_home= options.install_home,
            disable_xul = options.disable_xul,
            disable_app = options.disable_app,
            disable_broker = options.disable_broker,
            disable_device = options.disable_device,
            python_exe=options.python_exe,
            log_dir=options.log_dir,
            director_cfg=options.config_filename,
            director_log_cfg=options.director_log_cfg,
            da_config=options.da_config,
            manager_config=options.manager_config,
            servicestation_workingdir=options.servicestation_workingdir,
        )
        create_config(cfg)
        sys.exit(0)


    # Load the system config:
    if not os.path.isfile(options.config_filename):
        print "The config file name '%s' wasn't found" % options.config_filename
        sys.exit(1)

    else:    
        # I need to set the locale before I import the director,
        # as this uses the __G_LANG_ID__ which won't have been set
        # yet.
        cfg = ConfigObj(infile=options.config_filename)

        # Ok, clear to import:
        import director.config
        director.config.set_cfg(options.config_filename)

        # Set up python logging if a config file is given:
        cfg = director.config.get_cfg()
        log_cfg = cfg.get('logconfig')
        
        if os.path.isfile(log_cfg):
            logging.config.fileConfig(log_cfg)

        else:
            # No log configuration file given or it has been overidden
            # by the user, just print out to console instead:
            hdlr = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            log.addHandler(hdlr)
            log.setLevel(logging.DEBUG)
            log.propagate = False


        from director import manager
        manager.Manager().main()

        
        
