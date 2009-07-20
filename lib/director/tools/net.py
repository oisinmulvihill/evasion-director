"""
:mod:`net` -- This provides handy utiliy functions for network services.
==============================================================================

.. module:: net
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides handy utiliy functions for network services.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. data:: PORT_RETRIES the amount of times get_free_port and wait_for_ready
will retry for by default.

.. autoclass:: director.controllers.Controller
   :members:

.. autofunction:: director.tools.net.get_free_port

"""
import socket
import urllib
import random
import logging


def get_log():
    return logging.getLogger('director.tools.net')


PORT_RETRIES = 40


class NoFreePort(Exception):
    """
    Raised when get_free_port was unable to find a free port to use.
    """


def get_free_port(retries=PORT_RETRIES):
    """Called to return a free TCP port that we can use.

    This function gets a random port between 2000 - 40000.
    A test is done to check if the port is free by attempting
    to use it. If its not free another port is checked

    :param retries: The amount of attempts to try finding
    a free port.

    """
    def fp():
        return random.randint(2000, 40000)

    free_port = 0
    while retries:
        retries -= 1
        free_port = fp()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('', free_port))
            try:
                s.close()
            except:
                pass
        except socket.error, e:
            # port not free, retry.
            get_log().info("getFreePort: port not free %s, retrying with another port." % free_port)

    if not free_port:
        raise NoFreePort("I can't get a free port after retrying!")

    get_log().info("getFreePort: Free Port %s." % free_port)

    return free_port


def wait_for_ready(self, port, host='localhost', retries=PORT_RETRIES):
    """
    Called to wait for a web application to respond to
    normal get requests.

    :param port: the port the web application is listening on.

    :param host: the host the web application is running on. 

    :param retries: The amount of attempts to try finding
    a free port.

    :returns: True: the web app ready.

    """
    returned = False
    
    URI = "http://%s:%s" % (host, port)

    while retries:
        get_log().info("wait_for_ready: (reties left:%d) check if we can get <%s>." % (retries, URI))
        retries -= 1
        try:
            urllib.urlopen(URI)
        except IOError, e:
            # Not ready yet. I should check the exception to
            # make sure its socket error or we could be looping
            # forever. I'll need to use a state machine if this
            # prototype works. For now I'm taking the "head in
            # the sand" approach.
            pass
        else:
            # success, its ready.
            returned = True
            break;

        time.sleep(0.8)

    return returned