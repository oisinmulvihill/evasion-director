import logging

from twisted.internet import reactor
from twisted.web import xmlrpc, static, server
from twisted.web.resource import Resource

import messenger


class XmlRpcServer(xmlrpc.XMLRPC):
    """
    """
    # Used to prevent actual send of messaging (testing only)
    testing = False

    log = logging.getLogger("director.proxydispatch.XmlRpcServer")


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

    def xmlrpc_kill(self):
        """Broadcasts a quit message to the director to quit the application
        """
        self.log.debug("xmlrpc_kill: sending EXIT ALL to manager")
        messenger.send(messenger.EVT('EXIT_ALL'), {})
        self.log.debug("xmlrpc_kill: sent EXIT ALL OK.")
        return 0


def setup(port, testing=False):
    """
    """
    log = logging.getLogger("director.proxydispatch.setup")
    x = XmlRpcServer()
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
    reactor.run()     
