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

The most common evasion-director controller used is the evasion-agency. This
manages "agents" which load Python package or Module to control devices,
services or anything. The agency provides a device tree of nodes which can be
referred to in an abstract fashion.

Message passing between Controllers, Agents and all interested parties can be
done using the evasion-messenger. This project part is currently being
rewritten to use ZeroMQ. Old versions used a combination of PyDispatch, Stomp,
Morbid Broker and Twisted. This messaging is entirely optional.

The evasion agency and director increment version in lock step. I'm currently
thinking of merging the agency with the director repository.


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

