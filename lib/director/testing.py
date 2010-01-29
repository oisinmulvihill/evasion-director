"""
:mod:`testing` -- This provides some handy testing controllers.
===============================================================

.. module:: testing
   :platform: Unix, MacOSX, Windows
   :synopsis: This provides some handy testing controllers.
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: director.testing.FakeViewpoint
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
        self.log = logging.getLogger('director.testing.FakeViewpoint')
        
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
        import messenger
        
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

