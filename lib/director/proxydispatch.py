from twisted.internet import reactor
from twisted.web import static, server
from twisted.web.resource import Resource

import messenger


def forward_event(data):
    """
    """
    messenger.send()
    
    

class Hello(Resource):

    def getChild(self, name, request):
        return self

    def render_POST(self, request):
        return '<html>Hello, GET world! I am located at %r. </html>' % (request.prepath)

    def render_POST(self, request):
        return '<html>Hello, GET world! I am located at %r. </html>' % (request.prepath)


def setup(port):
    site = server.Site(Hello())
    reactor.listenTCP(port, site)
