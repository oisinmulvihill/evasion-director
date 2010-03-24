import thread
import logging

# Lazy import as this causes autodoc and other tools problems on windows:
#from twisted.internet import reactor
#from twisted.web import static, server
#from twisted.web.resource import Resource
#from twisted.web import xmlrpc


from evasion import messenger


class XmlRpcServer:
    """
    """
    # Used to prevent actual send of messaging (testing only)
    testing = False

    log = logging.getLogger("evasion.director.proxydispatch.XmlRpcServer")


    def xmlrpc_ping(self):
        """Allow others to check we're running.
        """
        import datetime
        msg = "EvasionDirectorProxyDispatch: %s" % datetime.datetime.now()
        self.log.debug("ping received: returning '%s'." % msg)
        return msg

        
    def xmlrpc_dispatch(self, reply_evt, data):
        """Dispatch the given data as a reply event.
        """
        self.log.debug("xmlrpc_dispatch: sending reply event '%s' with data '%s'" % (reply_evt, data))

        if self.testing:
            self.log.debug("xmlrpc_dispatch: Send disabled in testing mode.")
        else:
            reply = messenger.EVT(reply_evt)
            
            #This would require the waiting source to reply confirming receipt:
            #self.log.debug("xmlrpc_dispatch: sending, waiting for confirmation receipt.")
            # messenger.send_await(reply, data)

            # This will just send without waiting.
            self.log.debug("xmlrpc_dispatch: sending (no reply looked for)")
            messenger.send(reply, data)
            
            self.log.debug("xmlrpc_dispatch: sending (no reply looked for - SENT OK")

        return 0


    def xmlrpc_viewpoint_startup(self):
        """Broadcasts a EVT_VIEWPOINT_STARTUP message if anyone is listening they will react.
        """
        self.log.debug("xmlrpc_startup: sending EVT_VIEWPOINT_STARTUP to the director.")
        messenger.send(messenger.EVT('EVT_VIEWPOINT_STARTUP'), {})
        self.log.debug("xmlrpc_startup: sent EVT_VIEWPOINT_STARTUP OK.")

        return 0


    def xmlrpc_viewpoint_shutdown(self):
        """Broadcasts a EVT_VIEWPOINT_SHUTDOWN message if anyone is listening they will react.
        """
        self.log.debug("xmlrpc_shutdown: sending EVT_VIEWPOINT_SHUTDOWN to the director.")
        messenger.send(messenger.EVT('EVT_VIEWPOINT_SHUTDOWN'), {})
        self.log.debug("xmlrpc_shutdown: sent EVT_SHUTDOWN OK.")

        return 0


    def xmlrpc_exitall(self):
        """Sends a EVT_DIRECTOR_EXIT_ALL which will tell the director to shut all parts down
        in an orderly fashion.
        """
        def sendexit(data):
            self.log.debug("xmlrpc_exitall: sending EVT_DIRECTOR_EXIT_ALL to the director.")
            messenger.send(messenger.EVT('EVT_DIRECTOR_EXIT_ALL'), {})
            self.log.debug("xmlrpc_exitall: sent EVT_DIRECTOR_EXIT_ALL OK.")

        # be nice, return so otherside can close without errors.
        thread.start_new_thread(sendexit, (0,))

        return 0


def setup(port, testing=False):
    """
    """
    from twisted.internet import reactor
    from twisted.web import static, server
    from twisted.web.resource import Resource

    log = logging.getLogger("evasion.director.proxydispatch.setup")

    from twisted.web import xmlrpc    
    
    class Tw(xmlrpc.XMLRPC, XmlRpcServer):
        """Hack, to avoid import time select install in twisted"""
        pass
    
    x = Tw()
    x.testing = testing
    site = server.Site(x)
    
    reactor.listenTCP(port, site)
    log.info("XML-RPC proxy dispatch server setup ok (port:%s)" % (port))


if __name__ == "__main__":
    """
    """
    import logging
    from director import utils
    utils.log_init(logging.DEBUG)
    log = logging.getLogger("test proxydispatch.")
    
    setup(9001, testing=True)
    log.info("started on port 9001")
    
    from twisted.internet import reactor
    reactor.run()     
