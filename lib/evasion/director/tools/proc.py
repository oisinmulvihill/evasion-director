"""
:mod:`proc` -- This provides handy utiliy functions dealing with processes.
==============================================================================

.. module:: evasion.director.tools.proc
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides handy utiliy functions for network services.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>


.. autofunction:: evasion.director.tools.proc.pkill

.. autofunction:: evasion.director.tools.proc.kill

.. autofunction:: evasion.director.tools.proc.check

.. autofunction:: evasion.director.tools.proc.call

"""
import os
import sys
import logging
import subprocess


def get_log():
    return logging.getLogger('evasion.director.tools.proc')


def pkill(cmd):
    """
    Kill a process running base on it image name.
    
    On the windows the taskkill.exe command is used.

    On all other platforms pkill is used directly.

    :param cmd: This the string of the image or process name
    to kill depending on which platform you are on.
    
    """

    if sys.platform.startswith('win'):
        cmd = "taskkill.exe /F /T /IM %s " % cmd
    else:
        cmd = "pkill -9 %s" % cmd

    try:
        retcode = subprocess.call(cmd, shell=True)
        get_log().info("pkill: kill call successfull <%s>" % retcode)
        
    except OSError, e:
        get_log().warn("pkill: call failure %s " % str(e))


def kill(pid):
    """
    Stop the given process and kill all the processes in its
    process group, leaving no orphaned processes.

    :param pid: This the process id we wish to stop. 

    """
    get_log().info("kill: pid <%s>" % pid)

    if sys.platform.startswith('win'):
        cmd = "taskkill.exe /F /T /PID %s " % pid            
        get_log().info("kill: cmd <%s>" % cmd)
       
        try:
            retcode = subprocess.call(cmd, shell=True)
            get_log().info("kill: taskkill return code <%s>" % retcode)
           
        except OSError, e:
            get_log().warn("kill: didn't run <%s> Not on winxp?" % str(e))
           
    else:
        import signal
        pgid = os.getpgid(pid)
        get_log().info("kill: killing process group <%s> for pid <%s>" % (pgid, pid))
        os.killpg(pgid, signal.SIGHUP)


def check(subproc):
    """
    Called to check if the process is currently running.

    :param subproc: This is an instance of a running
    subprocess.Popen instance.

    :returns: True for process is running otherwise False.
    
    """
    returned = False

    if subproc and subproc.poll() is None:
        returned = True
        
    return returned

    
def call(cmd):
    """
    Called to run a command an return its output and return code.

    :param cmd: This a string representing a command 
    that can be run in the shell.

    :returns: (rc, stdout, stderr)
    
    """
    rc = 1
    out = ''
    err = ''
    
    try:
        get_log().info("call: running command <%s>" % cmd)
        r = subprocess.Popen(
            cmd, 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = r.communicate()
        rc = r.returncode

    except OSError, e:
        err = "Error - %s" % str(e)
        get_log().warn("call: Error <%s>" % err)
    
    else:
        get_log().info("call: command <%s> run %s" % (cmd, rc))
    
    return (rc, out, err)
    
    
