# -*- coding: utf-8 -*-
"""
:mod:`agency.agents.base.service`
==================================

.. module:: 'agency.agents.base.service'
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>


.. autoclass:: agency.agents.base.service.ServiceDevice
   :members:
   :undoc-members:

.. autoclass:: agency.agents.base.service.FakeViewpointDevice
   :members:
   :undoc-members:

"""
import time
import socket
import thread
import logging
import SocketServer
import SimpleHTTPServer
import SimpleXMLRPCServer


from evasion.agency import agent




class ControlFrameRequest(SocketServer.StreamRequestHandler):
    """Handle a viewpoint control frame request.
    """
    def handler(self):
        """
        self.rfile = request, self.wfile = response
        """


class StoppableTCPServer(SocketServer.TCPServer):
    """Handle requests but check for the exit flag setting periodically.
    """
    log = logging.getLogger('evasion.agency.agents.base.service.StoppableTCPServer')

    exitTime = False

    allow_reuse_address = True

    def __init__(self, serveraddress, ControlFrameRequest):
        SocketServer.TCPServer.__init__(self, serveraddress, ControlFrameRequest)

    def stop(self):
        self.exitTime = True
        self.log.info("Stop: set exit flag and closed port.")

    def server_bind(self):
        SocketServer.TCPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        """Handle a request/timeout and check the exit flag.
        """
        while not self.exitTime:
            try:
                returned = self.socket.accept()
                if len(returned) > 1:
                    conn, address = returned
                    conn.settimeout(None)
                    returned = (conn, address)
                return returned
            except socket.timeout:
                pass



class StoppableXMLRPCServer(
        SocketServer.ThreadingMixIn,
        SimpleXMLRPCServer.SimpleXMLRPCServer
    ):
    """Handle requests but check for the exit flag setting periodically.

    This snippet is based example from:

        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/425210

    """
    log = logging.getLogger('evasion.agency.base.service.StoppableXMLRPCServer')

    exitTime = False

    allow_reuse_address = True

    def stop(self):
        self.exitTime = True
        self.log.info("Stop: set exit flag and closed port.")

    def server_bind(self):
        SimpleXMLRPCServer.SimpleXMLRPCServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        """Handle a request/timeout and check the exit flag.
        """
        while not self.exitTime:
            try:
                returned = self.socket.accept()
                if len(returned) > 1:
                    conn, address = returned
                    conn.settimeout(None)
                    returned = (conn, address)
                return returned
            except socket.timeout:
                pass



class ServiceDevice(agent.Base):
    """An XML-RPC interface agent.

    Valid example configuration for this agent is:

        [myservice_name]
        cat = service
        agent = <your package with Agent class derived from ServiceDevice>
        interface = 127.0.0.1
        port = 8810

    The interface and port are where to start the XML-RPC server on.
    Once its up and running then you can access the interface at:

        'http://interface:port/'

    """
    log = logging.getLogger('evasion.agency.base.service.ServiceDevice')

    def __init__(self):
        self.config = None


    def registerInterface(self):
        """Register an instances who's members form the XML-RPC interace.

        Example Returned:

            class MyService(object):
                def ping(self):
                    return 'hello'

            return MyService()

        In this example, the ping() method will then be available when
        the service is started.

        """
        raise NotImplemented("Please implement this method!")


    def setUp(self, config):
        """Create the XML-RPC services. It won't be started until
        the start() method is called.
        """
        self.config = config
        interface = config.get('interface')
        port = int(config.get('port'))
        while True:
            try:
                self.log.info("Creating service...")
                self.server = StoppableXMLRPCServer((interface, port))

            except socket.error, e:
                if e[0] == 48 or e[1] == 'Address already in use':
                    self.log.error("Address (%s, %s) in use. Retrying..." % (
                        interface,
                        port
                    ))

            except Exception, e:
                self.log.exception("Service creation failed - ")
                break

            else:
                self.log.info("Service created OK.")
                break

            time.sleep(1)

        self.server.register_instance(self.registerInterface())


    def tearDown(self):
        """Stop the service.
        """
        self.stop()


    def start(self):
        """Start xmlrpc interface.
        """
        def _start(data=0):
            i = self.config.get('interface')
            p = self.config.get('port')
            self.log.info("XML-RPC Service URI 'http://%s:%s'" % (i,p))
            try:
                self.server.serve_forever()
            except TypeError:
                # caused by ctrl-c. Its ok
                pass

        thread.start_new_thread(_start, (0,))


    def stop(self):
        """Stop xmlrpc interface.
        """
        if self.server:
            self.server.stop()



class WebServerAgent(agent.Base, SimpleHTTPServer.SimpleHTTPRequestHandler):
    """A simple stoppable HTTP Web server agent to base REST agents on.

        [rest_service_agent]
        #disabled = 'yes'
        cat = service
        agent = <your package with Agent class derived from WebServerAgent>

        # Where to to bind the server to:
        interface = 0.0.0.0
        port = 39475

    """

    def setUp(self, config):
        """Create the services. It won't be started until
        the start() method is called.
        """
        self.config = config
        interface = config.get('interface')
        port = int(config.get('port'))

        class ToSelfRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
            """I need to provide a class to handle a request not an instance.
            This achieves this and routes to calls to the Agent do_* methods
            instead, passing in the re
            """
            parent = self
            def do_GET(self):
                self.parent.do_GET(self)
            def do_POST(self):
                self.parent.do_POST(self)
            def do_PUT(self):
                self.parent.do_PUT(self)
            def do_DELETE(self):
                self.parent.do_DELETE(self)

        while True:
            try:
                self.log.info("Creating service...")
                self.server = StoppableTCPServer(
                    (interface, port),
                    ToSelfRequestHandler
                )

            except socket.error, e:
                if e[0] == 48 or e[1] == 'Address already in use':
                    self.log.error("Address (%s, %s) in use. Retrying..." % (
                        interface, port
                    ))

            except Exception, e:
                self.log.exception("Service creation failed - ")
                break

            else:
                self.log.info("Service created OK.")
                break

            time.sleep(1)


    def tearDown(self):
        """Stop the service.
        """
        self.log.info("stop: Stopping Web Service.")
        self.stop()


    def defaultResponseHandler(self, request_handler):
        """A reference for how you can respond to a do_* request.

        :param request_handler: An instance of SimpleHTTPRequestHandler.

        """
        self.log.debug("defaultResponseHandler: source {0} - {1}".format(
            request_handler.client_address,
            request_handler.path,
        ))

        data = ""

        try:
            self.log.debug("defaultResponseHandler: recovering content")
            length = int(request_handler.headers.getheader('content-length', 0))
            self.log.debug("defaultResponseHandler: content length {}".format(
                length
            ))
            if length:
                data = request_handler.rfile.read(length)
            else:
                self.log.info("defaultResponseHandler: Content length header not set or 0! No data recovered.")

        except Exception as exc:
            self.log.error(
                "defaultResponseHandler ERROR: {0}/{1}({2})".format(
                    type(self).__name__, type(exc).__name__, str(exc)
                )
            )
            self.log.debug("defaultResponseHandler ERROR. Responding 500.")
            request_handler.send_response(500, "Service Error :(")

        else:
            self.log.debug("defaultResponseHandler: Responding 200.")
            request_handler.send_response(200, "OK")

        finally:
            request_handler.finish()

        return data


    def do_GET(self, request_handler):
        """Handle a GET request, override to implement.
        """
        self.log.info("do_GET: received request, responding.")
        self.defaultResponseHandler(request_handler)


    def do_POST(self, request_handler):
        """Handle a GET request, override to implement.
        """
        self.log.info("do_POST: received request, responding.")
        self.defaultResponseHandler(request_handler)


    def do_PUT(self, request_handler):
        """Handle a PUT request, override to implement.
        """
        self.log.info("do_PUT: received request, responding.")
        self.defaultResponseHandler(request_handler)


    def do_DELETE(self, request_handler):
        """Handle a DELETE request, override to implement.
        """
        self.log.info("do_DELETE: received request, responding.")
        self.defaultResponseHandler(request_handler)


    def start(self):
        """Start HTTP Web Server.
        """
        def _start(data=0):
            i = self.config.get('interface')
            p = self.config.get('port')
            self.log.info("Web Service URI 'http://%s:%s'" % (i,p))
            try:
                self.server.serve_forever()
            except TypeError:
                # caused by ctrl-c. Its ok
                pass

        thread.start_new_thread(_start, (0,))


    def stop(self):
        """Stop HTTP Web Server.
        """
        if self.server:
            self.server.stop()
