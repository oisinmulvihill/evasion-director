"""
:mod:`config` -- This supervises then agents under its control.
=================================================================

.. module:: evasion.director.config
   :platform: Unix, MacOSX, Windows
   :synopsis: This supervises then agents under its control.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module provides the director configuration parsing and handling.

.. autoexception:: evasion.director.config.ConfigInvalid

.. autoexception:: evasion.director.config.ConfigNotSetup

.. autoexception:: evasion.director.config.ConfigError

.. autoexception:: evasion.director.config.ControllerReloadError

.. autoclass:: evasion.director.config.ConfigStore
   :members:

.. autofunction:: evasion.director.config.clear

.. autofunction:: evasion.director.config.get_cfg

.. autofunction:: evasion.director.config.set_cfg

.. autofunction:: evasion.director.config.update_objs

.. autofunction:: director.config.recover_objects

.. autofunction:: director.config.webadmin_modules

.. autofunction:: director.config.load_agents

.. autofunction:: director.config.load_controllers

.. autofunction:: director.config.reload_controller

"""
import logging
import StringIO
import configobj
import itertools
import threading


from configobjs import *


def get_log():
    return logging.getLogger('evasion.director.config')


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


class ControllerReloadError(Exception):
    """
    Raise by reload_controller for problems it encounters.
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

    The list of configuration objects is stored in the cfg member variable.

    The ConfigObj instance is stored as the 'configobj' member variable.

    The director, broker, agency and webadmin are members which will
    not be None. These will be set up if the are present in the cfg
    configuration objects.

    """
    def __init__(self, raw, cfg, configobj, filename):
        """
        Set up the config store for later reference via
        get_config() / set_config() / update_config()

        :param raw: The raw string contents of the original
        config file.

        :param cfg: The list of recovered config objects.

        :param configobj: The original configobj.ConfigObj
        instance which contains the origial processed raw
        config.

        :param filename: The file name and path to save
        changes to or reload from.

        """
        self.raw = raw
        self.cfg = cfg
        self.configobj = configobj
        self.filename = filename

        # Quick access. Director will always be present.
        # The others depend on the configuration.
        self.director = None
        self.broker = None
        self.agency = None
        self.webadmin = None
        self.findInstances()


    def findInstances(self):
        """
        Locate director, broker, agency and webadmin instances
        in the cfg objects and store them as attributes for easy
        access.

        """
        for i in self.cfg:
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

    # Won't work once module imports are added:
    #__configLock.acquire()
    #try:
    #    rc =  copy.deepcopy(__config)
    #finally:
    #    __configLock.release()
    #
    #return rc

    return __config


def update_objs(cfg_objs):
    """Called to updated the current store of config objs.

    :param cfg_objs: this is a list of configuration objects
    as returned by a call from recover_objects.

    This function will typically be done after a load_agents,
    load_controllers or reload_controller.

    If no config has been set up, via a call to set_config, then
    ConfigNotSetup will be raised to indicate so.

    """
    global __config
    if not __config:
        raise ConfigNotSetup("No configuration has been setup.")

    __configLock.acquire()
    try:
        __config = ConfigStore(
            cfg=cfg_objs,
            # reuse the old instances versions of these:
            raw=__config.raw,
            configobj=__config.configobj,
            filename=__config.filename
        )
    finally:
        __configLock.release()


def set_cfg(raw, filename=''):
    """Called to set up the configuration used for the project.

    :param raw: this is a string representing the raw
    configuration data read from the config file.

    :param filename: this is a the file name and path
    of the original configuration file. This will be
    used to save or reload the configuration from if
    needed at a later stage.

    """
    global __config

    # Recover the objects and store them:
    cfg_objs = recover_objects(raw)

    __configLock.acquire()
    try:
        __config = ConfigStore(
            raw,
            cfg_objs,
            configobj.ConfigObj(StringIO.StringIO(raw)),
            filename
        )
    finally:
        __configLock.release()


def save_cfg(filename=None):
    """Called to write the configuration to disk after
    updating the internal configobj instance.
    """
    global __config

    __configLock.acquire()
    try:
        # Lock other's out of saving until I've finished.
        pass

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

    :param config: This is a string representing the contents
    of the configuration file.

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
            # store the config dict section
            c.config = s

        def recover(self, section):
            """Convert to configobjs"""
            skip = False
            rsection = cfg[section]
            if section in MAPPED_SECTIONS:
                default_order, container = MAPPED_SECTIONS[section]
                container = container()
                if 'name' in rsection:
                    # remove this if its present in favour of hardcoded values.
                    rsection.pop('name')
                if 'order' not in rsection:
                    container.order = default_order
                if section == 'director':
                    self.director = container
                    self.director.messaging = rsection.get('messaging', 'no')
                    #get_log().debug("recover_objects: 'director' found.")
                if section == 'broker':
                    self.broker = container
                    #get_log().debug("recover_objects: 'broker' found.")
                if section == 'agency':
                    self.agency = container
                    #get_log().debug("recover_objects: 'agency' found.")
                if section == 'webadmin':
                    self.webadmin = container
                    #get_log().debug("recover_objects: 'webadmin' found.")
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
                # Ignore so I can have logging as part of the director
                # configuration.
                get_log().info("recover_objects: unknown section, skipping '%s'." % (section))
                skip = True
                # if 'drignore' in cfg[section]:
                    # get_log().info("recover_objects: skipping section '%s' as 'drignore' is present." % (section))
                    # return
                # container = Container()
                # self.setup(container, rsection)
                # container.name = section
                # if 'order' not in rsection:
                #    # container.order = self.sectionCounter.next()

            if not skip:
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
        try:
            imported_agent = __import__(importmod, fromlist=fromlist, level=0)
        except TypeError, e:
            # possibly running under python24, retry in a compatible way:
            imported_agent = __import__(importmod, globals(), locals(), fromlist)
            #print "imported_agent: ", imported_agent

    except ImportError, e:
        get_log().error("Error loading '%s', it raised the error: '%s'." % (importmod, str(e)))
        raise ImportError("The controller '%s' from '%s' could not be imported! %s" % (
            importmod,
            obj,
            str(e)
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


def load_controllers(config_objs, ignore_exceptions=False):
    """Called to test and then load the controllers from the configuration.

    :param config_objs:
        This is a list as returned by recover_objects()

    :param ignore_exceptions:
        True means a module will be ignored if it causes an
        exception will being loaded.

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
            if ignore_exceptions:
                try:
                    obj.mod = import_module(obj.type, obj)
                except:
                    get_log().exception("load_controllers: the module '%s' could not import - " % (obj))

            else:
                obj.mod = import_module(obj.type, obj)


    [doimp(obj) for obj in config_objs]

    return config_objs



def reload_controller(name, new_config):
    """
    Called replace a controller entry and (re)load the
    controller based on

    :params name: This is the string section name as
    found in the configuration which is also the
    controller name.

    :params new_config: This is any valid dict representing
    a valid entry as a controller. For Example::

        new_config = dict(
                order = 4,
                name = "mycontroller",
                disabled = 'no',
                controller = 'mypackage.mycontroller2'
                :
                user args
            )

    :returns: None

    The system wide configuration will have been updated with
    the new controller.

    """
    # Find the controller in the configuration
    c = get_cfg()

    ctrl = None
    for c in c.cfg:
        if c.name == name:
            ctrl = c
            break

    if not ctrl:
        msg = "Unable to find the controller '%s' in the configuration!" % name
        get_log().error("reload_controller: %s")
        raise ControllerReloadError(msg)

    get_log().debug("reload_controller: found controller '%s'." % ctrl)

    # Stop the controller if its running:
    #
    if ctrl.mod:
        get_log().debug("reload_controller: '%s' has a loaded module '%s'." % (ctrl, ctrl.mod))
        if ctrl.mod.isStarted():
            get_log().debug("reload_controller: '%s' stopping." % ctrl)
            ctrl.mod.stop()

        ctrl.mod.stop()

        # Clean up the controller:
        get_log().debug("reload_controller: ctrl.mod '%s' calling tearDown()." % (ctrl.mod))
        ctrl.mod.tearDown()

    # Create a new controller using the new_config
    #
    get_log().debug("reload_controller: creating new controller.")
    container = Controller()
    for key, value in new_config.items():
        #get_log().debug("reload_controller: setting key '%s' to value '%s' on '%s' " % (key, value, container))
        if key == 'order':
            # Make these numbers and not strings.
            value = int(value)
        setattr(container, key, value)

    container.config = new_config
    container.name = name
    if 'order' not in new_config:
        get_log().debug("reload_controller: no order found using old controllers order '%s'." % ctrl.order)
        container.order = ctrl.order

    # Check the controller is ok:
    get_log().debug("reload_controller: validating new controller.")
    container.validate()

    # Attempt to load the controller module if it is not disabled:
    disabled = new_config.get('disabled', 'no')
    if disabled == 'no':
        m = container.controller
        get_log().debug("reload_controller: new controller isn't disabled. Loading module '%s'." % m)
        container.mod = import_module('Controller', container)

        # We need to call the modules setUp()
        get_log().debug("reload_controller: Calling new modules '%s' setUp." % container.mod)
        container.mod.setUp(new_config)

    # Remove the old controller and replace it with the new one:
    get_log().debug("reload_controller: Removing old controller '%s' from system config." % ctrl)
    c = get_cfg()
    current_list = c.cfg
    new_list = [container,]
    for c in current_list:
        if c.name != name:
            new_list.append(c)

    # Re-order the config objects
    reordered = [(c.order, c) for c in new_list]
    reordered.sort()

    get_log().debug("reordered: %s" % reordered)
    cfg_objs = [c[1] for c in reordered]
    get_log().debug("cfg_objs: %s " % cfg_objs)

    # Store the newly sorted and updated config objects:
    get_log().debug("reload_controller: updating system wide configuration.")
    update_objs(cfg_objs)

    # Finally update the the original configobj instance section
    # for this controller. This will allow changes to be saved.
    #
    get_log().debug("reload_controller: updating configobj instance with new config for section '%s'." % name)
    c = get_cfg()
    c.configobj[name] = new_config


def export_configuration():
    """
    Called to return the get_cfg() in a form that can travel i.e. pickle

    :returns:

        returned = dict(
            cfg = [..list of controller dicts from export call..],
            filename = '..name and path of config..',
            director = '' | director.export(),
            agency = '' | agency.export(),
            broker = '' | broker.export(),
            webadmin = '' | webadmin.export(),
        )

    """
    c = get_cfg()

    returned = dict(
        cfg = [co.export() for co in c.cfg],
        filename = c.filename,
        director = '',
        agency = '',
        broker = '',
        webadmin = '',
    )

    if c.director:
        returned['director'] = c.director.export()

    if c.agency:
        returned['agency'] = c.agency.export()

    if c.broker:
        returned['broker'] = c.broker.export()

    if c.webadmin:
        returned['webadmin'] = c.webadmin.export()

    return returned
