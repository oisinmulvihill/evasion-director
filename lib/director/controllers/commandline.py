"""
:mod:`commandline` -- This provides the interface to command line processes.
=============================================================================

.. module:: config
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides the interface to command line processes.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This module provides the director configuration parsing and handling. 

.. autoclass:: director.config.Container
   :members:
   :undoc-members:

"""
import subprocess

import base



class Controller(base.Controller):
    """
    This is the command line controller that implements the
    launching of processes via pythons subprocess module.

    This controller typically adds two extra options to the
    standard controller configuration::

        [my_proc_name]
        # Standard options example:
        disabled = 'no'
        order = 1
        controller = ...

        # Command Line specific options:
        command = 'mycommand -someoption -anotheroption=abc'
        workingdir = '/tmp'

    The command is the shell based command you would call if
    you were running the command out side of the director.

    The workingdir is the place on the file system in which
    the process wil be run. You could place files your command
    needs there and it will find them in the current path.

    """
