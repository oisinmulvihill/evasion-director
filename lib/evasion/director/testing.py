"""
:mod:`testing` -- This provides some handy testing controllers.
===============================================================

.. module:: testing
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides some handy testing controllers.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: evasion.director.testing.FakeViewpoint
   :members:
   :undoc-members:

"""
import logging
import threading

from pydispatch import dispatcher



class FakeViewpoint(object):
    """This provides a 'viewpoint' signal handler you can use
    in test to receive events that would normally be handled
    by the evasion-viewpoint.

    """
    def __init__(self, uri):
        """
        :param uri: This is the uri to return when we receive
        get URI requests.

        """
        self.log = logging.getLogger('evasion.director.testing.FakeViewpoint')

        # This is returned when we receive a get uri request.
        # This will also be updated and set to that from a set
        # uri request.
        self.uri = uri

        # replace content requests go here (id, content)
        self.replaceList = []

        # Hook into the signals normally handled by the viewpoint:
        dispatcher.connect(
            self.onGetUri,
            signal="VIEWPOINT_GET_URI",
        )
        self.getUriOccured = threading.Event()

        dispatcher.connect(
            self.onSetUri,
            signal="VIEWPOINT_SET_URI",
        )
        self.setUriOccured = threading.Event()

        dispatcher.connect(
            self.onReplace,
            signal="VIEWPOINT_REPLACE",
        )
        self.replaceOccured = threading.Event()


    def __del__(self):
        dispatcher.disconnect(self.onGetUri)
        dispatcher.disconnect(self.onSetUri)
        dispatcher.disconnect(self.onReplace)


    def reply(self, messenger_event, data):
        """Called to handle the reply for a VIEWPOINT_* command event.
        """
        # Lazy import so unless this class is used its import won't be needed.
        from evasion import messenger

        # The uid of the signal is used as the 'address' that
        # a reply goes back to. We'll forward the replyto which
        # the xul browser will return to us later. The method
        # dataReceived then deal with the business of sending a
        # reply.
        reply_to = messenger_event.uid

        self.log.debug("replyTo: dispatching reply to <%s:%s>." % (
            messenger_event, reply_to
        ))

        messenger.reply(messenger_event, data)


    def onGetUri(self, signal, sender, **kw):
        """Call to handle the VIEWPOINT_GET_URI event.
        """
        self.log.debug("""onGetUri (VIEWPOINT_GET_URI): kw:%s returning '%s'.""" % (kw, self.uri))
        self.reply(signal, self.uri)

        # Indicate that we received an get uri event:
        self.getUriOccured.set()


    def onSetUri(self, signal, sender, **kw):
        """Call to handle the VIEWPOINT_SET_URI event.
        """
        self.log.debug("""onSetUri (VIEWPOINT_SET_URI): %s""" % (kw))

        data = kw['data']
        uri = data['uri']

        self.log.info("onSetUri: uri '%s'." % (uri))
        self.uri = uri

        self.reply(signal, uri)

        # Indicate that we received an set uri event:
        self.setUriOccured.set()


    def onReplace(self, signal, sender, **kw):
        """Call to handle the VIEWPOINT_REPLACE event.
        """
        self.log.debug("""onReplace (VIEWPOINT_REPLACE): %s""" % (kw))

        data = kw['data']
        content_id = data['content_id']
        content = data['content']

        # Store what should have been replaced:
        self.replaceList.append(
            (content_id, content)
        )

        self.reply(signal, '')

        # Indicate that we received an replace event:
        self.replaceOccured.set()


def setup_broker(port=61613, interface='127.0.0.1'):
    """
    Called to start the internal broker listening
    via twisted's reactor.

    :param port: TCP port to listen on (default 61613)

    :param interface: The interface to bind to (default
    127.0.0.1):

    :returns: This returns a listening port instance
    on which deferred = listener.stopListening() can
    be called.

    Ref:
    http://twistedmatrix.com/documents/8.2.0/api/twisted.internet.interfaces.IReactorTCP.listenTCP.html

    """
    # lazy import to prevent import issues if were not using this function.
    from twisted.internet import reactor
    from evasion.director.morbid import setup
    return setup(reactor, port, interface)


def director_setup(test_config, **kw):
    """
    Create a director manager instance which can be used
    from unit/acceptance/functional tests.

    :param test_config: this is a valid director config
    string as you would have in its config file.

    :returns: A instance of director.manager:Manager

    """
    # lazy import to prevent loops:
    from evasion import director
    from evasion.director import manager
    from evasion.director.tools import net

    broker_interface = kw.get('broker_interface', '127.0.0.1')
    broker_port = kw.get('broker_port', net.get_free_port())
    broker_channel = kw.get('broker_channel', 'evasion')
    proxy_port = net.get_free_port(exclude_ports=[broker_port,])
    proxy_port = kw.get('proxy_port', proxy_port)

    # load this configuration into the director:
    #
    director.config.clear()
    director.config.set_cfg(test_config % locals())
    director.config.get_cfg()

    # Create the director management logic:
    #
    m = manager.Manager()
    m.main(director_testing=True)
    m.appmainSetup() # need this as mainloop is not in main now.

    return dict(
        manager=m,
        broker_interface=broker_interface,
        broker_port=broker_port,
        broker_channel=broker_channel,
        proxy_port=proxy_port,
    )

