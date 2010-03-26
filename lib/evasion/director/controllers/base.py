"""
:mod:`base` -- This is the base interface for a controller which the director can load.
========================================================================================

.. module:: evasion.director.controllers.base
   :platform: Unix, MacOSX, Windows
   :synopsis: This is the base interface for a controller which the director can load.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

This is the base interface for a controller which the director can load.

.. autoclass:: evasion.director.controllers.base.FailedToStart
   :members:

.. autoclass:: evasion.director.controllers.base.FailedToStop
   :members:

.. autoclass:: evasion.director.controllers.base.Controller
   :members:
   :undoc-members:

"""

__all__ = ['FailedToStart', 'FailedToStop', 'Controller']


class FailedToStart(Exception):
    """
    This is raised to indicate to the director that the process
    did not start successfully.

    The isStarted method of a Controller instance will usually
    raise this.
    
    """

class FailedToStop(Exception):
    """
    This is raised to indicate to the director that the process
    did not start successfully.

    The isStopped method of a Controller instance will usually
    raise this.

    """


class Controller(object):
    """
    This class represents a 'process' which the director will manage.
    This class is really an interface which all who wish to be loaded
    must derive from.
    
    """        
    def setUp(self, config):
        """
        This is called after the controller has been created to perform
        any needed process set up by the controller instance. This is
        called usually when the director has first started.

        No process should be started at this point.

        :param config: This is the confiration section recovered when
        the configuration was parsed.

        :return: None
        
        """
        self.config = config
        

    def start(self):
        """
        This is called to start the process that was set up in an earlier
        call to the setup(...) method.

        This method should not block waiting for the process to start. The
        director will call the isRunning method to wait for your process
        to be ready for duty.

        This method can potentially be called again after a call to stop,
        bear this in mind.

        :return: None
        
        """


    def isStarted(self):
        """
        This is called to wait for the process to finish loading and report
        is ready.

        This method is called directly after a call to the start method and
        it is acceptable to block waiting.

        :return: True if the process is running otherwise False
        
        """
        return False
    

    def stop(self):
        """
        This is called to stop the process that was set up in an earlier
        call to the setup(...) method.

        This method can potentially be called again after a call to start,
        bear this in mind.

        :return: None
        
        """
        return False


    def isStopped(self):
        """
        This is called to wait for the process to finish stopping.

        This method is called directly after a call to the stop method and
        it is acceptable to block waiting.

        :return: True if the process has stopped otherwise False
        
        """


    def tearDown(self):
        """
        This is called usually when the director is shutting down. The
        process stop will have been called prior to this method. The
        process only needs to free or perform and needed clean up here.

        :return: None
        
        """

