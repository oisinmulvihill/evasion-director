"""
Oisin Mulvihill
2007-05-18

"""
import os
import sys
import os.path
import logging
import ConfigParser
import logging.config
from optparse import OptionParser


def get_log():
    return logging.getLogger("evasion.director.scripts.main")


DEFAULT_CONFIG_NAME = "director.cfg"
DEFAULT_SERVICESTATION_NAME = "servicestation.cfg"


def render_config(cfg, template_data, outputfile):
    """Render the mako template to plain text or print useful traceback for missing config variables.

    """
    ok = True

    # lazy import do this module can be included without import mako.
    import pprint
    from mako import exceptions
    from mako.template import Template

    def writeout(filename, data):
        # Ok, write the result out to disk:
        fd = open(filename, 'wb')
        fd.write(data)
        fd.close()

    try:
        data = Template(template_data, output_encoding='utf8', encoding_errors='strict').render(**cfg)
    except:
        ok = False
        get_log().debug("""Template data:
%s

outfile:
%s

""" % (pprint.pformat(cfg), outputfile))

        get_log().debug("""Error Create Template:
%s

""" % exceptions.text_error_template().render())

    else:
        writeout(outputfile, data)

    if not ok:
        sys.exit(1)




def create_config(cfg_dict):
    """Create the default director.ini in the current directory based
    on a the template stored in director.templatecfg

    """
    from evasion.director import templatecfg
    from pkg_resources import resource_string

    get_log().debug("Creating initial configuration.")

    # Fill in the template information with viewpoint path:
    cfg_dict['viewpoint_path'] = ''
    try:
        # Attempt to set up the path to the evasion viewpoint XUL app
        # installed as a python package.
        from evasion import viewpoint
    except ImportError:
        pass
    else:
        cfg_dict['viewpoint_path'] = os.path.abspath(viewpoint.__path__[0])

    # Fill in the template information with XUL Browser path:
    t = resource_string(templatecfg.__name__, 'director.cfg.mako')
    render_config(cfg_dict, t, DEFAULT_CONFIG_NAME)

    t = resource_string(templatecfg.__name__, 'servicestation.cfg.mako')
    render_config(cfg_dict, t, DEFAULT_SERVICESTATION_NAME)

    print("Success, '%s' and '%s' created ok." % (DEFAULT_CONFIG_NAME, DEFAULT_SERVICESTATION_NAME))


class StreamPassThrough:
    """
    Provide a means to channel stdout and stderror
    through the log set up.

    """
    def __init__(self, trap=False):
        self.trap = trap
        self.origStderr = sys.stderr
        self.origStdout = sys.stdout

        class Err:
            def __init__(self, parent):
                self.p = parent

            def write(self, msg):
                self.p.stderrWrite(msg)

        sys.stderr = Err(self)

        class Out:
            def __init__(self, parent):
                self.p = parent

            def write(self, msg):
                self.p.stdoutWrite(msg)

        sys.stdout = Out(self)

    def stderrWrite(self, msg):
        get_log().info('stderr: %s' % msg)
        if not self.trap:
            self.origStderr.write(msg)

    def stdoutWrite(self, msg):
        get_log().info('stdout: %s' % msg)
        if not self.trap:
            self.origStdout.write(msg)


def main():
    """
    """
    current_dir = "%s" % os.path.abspath(os.curdir)
    director_cfg = current_dir + os.path.sep + DEFAULT_CONFIG_NAME
    directorlog_output = current_dir + os.path.sep + 'director.log'

    parser = OptionParser()

    parser.add_option("--config", action="store", dest="config_filename",
                    default=director_cfg,
                    help="This director configuration file to use at run time."
                    )

    parser.add_option("--eat-exceptions", action="store_true", dest="eat_exceptions",
                    default=False,
                    help="Keep going if possible on Controller exceptions."
                    )

    parser.add_option("--logtoconsole", action="store_true", dest="logtoconsole",
                    default=False,
                    help="Override log setup from configuration and log to the console instead."
                    )

    parser.add_option("--create", action="store_true", dest="create_config",
                    default=False,
                    help="Create configuration files from the internal templates"
                    )

    parser.add_option("--installdir", action="store", dest="install_dir",
                    default=current_dir,
                    help=(
                        "Used with the --create to setup the install folder in which the director"
                        "is found in the generated configuration output."
                    ))

    parser.add_option("--exe", action="store", dest="exe",
                    default=r"director",
                    help=(
                        "Used with the --create to set the executeable name that servicestation calls"
                        "in its generated servicestation.ini."
                    ))

    parser.add_option("--logdir", action="store", dest="log_dir",
                    default=current_dir,
                    help=(
                        "Used with --create to set the folder the director.log file will"
                        "be written in the generated configuration output."
                    ))

    parser.add_option("--disableagency", action="store", dest="disable_agency",
                    default="no",
                    help=(
                        "Used with --create to disable the agency in the"
                        "generated configuration output."
                    ))

    parser.add_option("--disablebroker", action="store", dest="disable_broker",
                    default="no",
                    help=(
                        "Used with --create to disable the broker in the"
                        "generated configuration output."
                    ))

    parser.add_option("--servicestationdir", action="store", dest="servicestation_dir",
                    default=current_dir,
                    help=(
                        "Used with --create to set the servicestation install folder in the"
                        "generated configuration output."
                    ))

    parser.add_option("--directorcfg", action="store", dest="director_cfg",
                    default=director_cfg,
                    help=(
                        "Used with --create to set the path and name of the director configuration"
                        "servicestation will use in the generated configuration output."
                    ))

    parser.add_option("--directorlog_output", action="store", dest="directorlog_output",
                    default=directorlog_output,
                    help=(
                        "Used with --create to set the path and name of the director log output"
                        "file used in the generated configuration output."
                    ))
    parser.add_option("--logstdouterr", action="store_true", dest="logstdouterr",
                    default=False,
                    help="Filter stdout and stderr through our logging set up (default).")

    (options, args) = parser.parse_args()

    log = logging.getLogger("evasion.director.scripts.main.main")

    # Create the default app manager config:
    if options.create_config:
        cfg = dict(
            install_dir=options.install_dir,
            exe=options.exe,
            log_dir=options.log_dir,
            logconfig_filename='',
            disable_agency=options.disable_agency,
            disable_broker=options.disable_broker,
            servicestation_dir=options.servicestation_dir,
            director_cfg=options.director_cfg,
            directorlog_output=options.directorlog_output.replace('\\', '/'),
        )
        create_config(cfg)
        sys.exit(0)

    # Load the system config:
    if not os.path.isfile(options.config_filename):
        sys.stderr.write("The config file name '%s' wasn't found" % options.config_filename)
        sys.exit(1)

    else:
        def logtoconsolefallback(log):
            # Log to console instead:
            hdlr = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            log.addHandler(hdlr)
            log.setLevel(logging.DEBUG)
            log.propagate = False

        if not options.logtoconsole:
            # Set up logging from director.cfg
            try:
                logging.config.fileConfig(options.config_filename)
            except ConfigParser.NoSectionError:
                logtoconsolefallback(log)
                log.warn("No valid logging found in configuration. Using console logging.")
        else:
            logtoconsolefallback(log)

        # Filter stdout and stderr through logging now its up
        # and running to aid debug in case of problems
        #
        if options.logstdouterr:
            spt = StreamPassThrough()

        # Ok, clear to import:
        from evasion.director import config

        # Set up the director config and recover the object from it:
        cfg_file = os.path.abspath(options.config_filename)
        fd = file(cfg_file, 'rb')
        raw = fd.read()
        fd.close()

        config.set_cfg(raw, filename=cfg_file)

        from evasion.director import manager
        m = manager.Manager(
            eat_exceptions=options.eat_exceptions
        )
        try:
            m.main()
        except (KeyboardInterrupt, SystemExit):
            m.exit()
