Evasion Project
===============

.. contents::

Introduction
------------

The evasion project allows the creation of programs from configuration.

This is achieved by loading "controller sections" from configuration. A
controller is a Python package or module that provides some functionality.
It is given all the configuration inside its section. The evasion-director
manages controllers in a similar fashion to init.d on linux. The evasion
director starts up and loads each of the sections.

The most common evasion-director controller used is the evasion agency. This
manages "agents". An agent is a Python package or Module. Agents are used to
control hardware devices or services. The agency provides a device tree of
nodes which can be referred to in an abstract fashion.

Message passing between Controllers, Agents and all interested parties can be
done using the evasion-messenger. This project part is currently being rewritten
to use ZeroMQ. Old versions used a combination of PyDispatch, Stomp, Morbid
Broker and Twisted. This messaging is entirely optional.

Note: The evasion-agency project has been merged with the director code base.
The "evasion.agency" namespace is now provided by the evasion-director code
base.


Basic Examples
--------------

Simplest configuration
~~~~~~~~~~~~~~~~~~~~~~

The most basic example is using the minimal configuration "app.ini"::

    [director]
    messaging = 'no'

This can then be run from the command line::

    $ director --config app.ini
    2012-05-27 15:56:13,955 root WARNING No valid logging found in configuration. Using console logging.
    2012-05-27 15:56:14,001 evasion.director.manager.Manager WARNING Messaging disable as evasion-messenger is not installed.
    2012-05-27 15:56:14,001 evasion.director.manager.Manager INFO main: running.
    2012-05-27 15:56:14,001 evasion.director.manager.Manager INFO controllerSetup: loading controllers from config.
    2012-05-27 15:56:14,001 evasion.director.manager.Manager INFO controllerSetup: 1 controller(s) recovered.
    2012-05-27 15:56:15,576 evasion.director.manager.Manager WARNING Ctrl-C, Exiting.
    $

The only controller load is the "director" controller. This isn't very useful
as nothing is run.


Run a program
~~~~~~~~~~~~~

You can run and manage any type of command line program::

    [command_line_example]
    # Set this to 'yes' to stop this controller from being used.
    disabled = 'no'

    # This is optional and allows the order in which controllers are started
    # to be set.
    order = 1

    # Where the "Controller" class is to be found.
    controller = 'evasion.director.controllers.commandline'

    # The command line specific options:
    #
    # The command to run.
    command = 'ls'
    # Where the command is to be run from.
    workingdir = '/tmp'

Running this configuration gets::

    $ director --config app.ini
    root WARNING No valid logging found in configuration. Using console logging.
    evasion.director.manager.Manager INFO main: running.
    evasion.director.manager.Manager INFO controllerSetup: loading controllers from config.
    evasion.director.manager.Manager INFO controllerSetup: 2 controller(s) recovered.
    evasion.director.controllers.commandline DEBUG setUp: command <ls> workingdir </tmp>
    evasion.director.manager.Manager INFO appmain: The controller '<Controller: order:1 name:command_line_example disabled:no>' needs to be started.
    evasion.director.controllers.commandline INFO start:  'ls' running. PID 87808
    evasion.director.manager.Manager INFO appmain: Started ok 'command_line_example'? 'True'
    1564b4fc7dd26  ics41562  icssuis1316027648  launch-0FvLcQ  launch-7vMUyC  launch-9uZ0bO  launch-ASdWau  launch-RUjEPx  launchd-460.ZFsfn1
    evasion.director.manager.Manager INFO appmain: The controller '<Controller: order:1 name:command_line_example disabled:no>' needs to be started.
    evasion.director.controllers.commandline INFO start:  'ls' running. PID 87809
    evasion.director.manager.Manager INFO appmain: Started ok 'command_line_example'? 'True'
    1564b4fc7dd26  ics41562  icssuis1316027648  launch-0FvLcQ  launch-7vMUyC  launch-9uZ0bO  launch-ASdWau  launch-RUjEPx  launchd-460.ZFsfn1
    evasion.director.manager.Manager INFO appmain: The controller '<Controller: order:1 name:command_line_example disabled:no>' needs to be started.
    evasion.director.controllers.commandline INFO start:  'ls' running. PID 87810
    evasion.director.manager.Manager INFO appmain: Started ok 'command_line_example'? 'True'
    icssuis1316027648  launch-0FvLcQ  launch-7vMUyC  launch-9uZ0bO  launch-ASdWau  launch-RUjEPx  launchd-460.ZFsfn1
    evasion.director.manager.Manager WARNING Ctrl-C, Exiting.
    evasion.director.controllers.commandline INFO stop: stopping the process PID:'87810' and all its children.
    evasion.director.tools.proc INFO kill: pid <87810>
    evasion.director.controllers.commandline WARNING pkill: call failure [Errno 3] No such process
    $

The director loads the controller sections. Th commandline controller is
started. The "ls" command lists the contents of the "/tmp" directory. The
output is captured and logged. The director then notices that the command has
exited needs running again and the process repeats. The director will keep
running all "controllers" that make up the program.


Use the Agency
~~~~~~~~~~~~~~


Development Process
-------------------

The source code mangement and release process follows roughly the gitflow
process.

 * http://nvie.com/posts/a-successful-git-branching-model/
 * https://github.com/nvie/gitflow


Issues
------

All issues for the other evasion-* project parts should be logged on the
evasion-director project.

Other Docs
----------

I'm in the process of bring together various documents. For the moment
information can be found here:

EvasionProject code documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * http://www.evasionproject.com/apidocs/

EvasionProject Wiki
~~~~~~~~~~~~~~~~~~~

  * http://www.evasionproject.com/


Release Notes
-------------

1.1.6
~~~~~

The evasion-agency repository code has been merged with the evasion-director.
What this means in practice is the evasion-director now provides the
"evasion.agency" namespace. The director no longer depends on the
"evasion-agency".


1.1.5:
~~~~~~

In this release of fixed the issue "default behaviour change: failed controller
& agent imports cause exit.". The director will now exit when a controller
raises an exception.

 * https://github.com/oisinmulvihill/evasion-director/issues/7


1.1.4:
~~~~~~

GitHub Milestone for this release https://github.com/oisinmulvihill/evasion-director/issues?milestone=1&state=closed

Fixed
 * Re-raising SystemExit, KeyboardInterrupt: https://github.com/oisinmulvihill/evasion-director/issues/5
 * Handling unhandled exceptions: https://github.com/oisinmulvihill/evasion-director/issues/2
 * Agency assumes 'log' attribute is present in Agent: https://github.com/oisinmulvihill/evasion-director/issues/1

