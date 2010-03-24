#!/usr/bin/python

# Copyright (c) 2008 Michael Carter
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import traceback
import stomper
try:
    from twisted.internet.protocol import Factory, Protocol
except:
    import sys
    print >>sys.stderr, "Twisted required to run; see www.twistedmatrix.com"
    # TODO: does the error code matter more than being non-zero?
    #       -mcarter 8/30/08
    sys.exit(1)
    
class StompProtocol(Protocol):
    id = 0
    def __init__(self):
        self.state = 'initial'
        self.buffer = ""
        self.stompBuffer = stomper.stompbuffer.StompBuffer()
        self.lastNull = False
        StompProtocol.id += 1
        self.id = StompProtocol.id
        
    def dataReceived(self, data):
        # NOTE: Allow each frame to have an optional '\n'
        # NOTE: binary DOES NOT WORK with this hack in place
        self.stompBuffer.appendData(data.replace('\0', '\0\n'))

        while True:
            msg = self.stompBuffer.getOneMessage()
            
            # NOTE: the rest of the optional '\n' hack
            if self.stompBuffer.buffer.startswith('\n'):
                self.stompBuffer.buffer = self.stompBuffer.buffer[1:]
                
            if msg is None:
                break
#            print 'GOT MESSAGE', msg
            if not msg['headers'] and not msg['body'] and not msg['cmd']:
                break
            getattr(self, 'read_%s' % self.state)(**msg)

    def sendError(self, e):
        exception, instance, tb = traceback.sys.exc_info()
        tbOutput= "".join(traceback.format_tb(tb))      
        self.sendFrame('ERROR', {'message': str(e) }, tbOutput)
    
    def sendFrame(self, cmd, headers, body):
        f = stomper.Frame()
        f.cmd = cmd
        f.headers.update(headers)
        f.body = body
        self.transport.write(f.pack())
    
    def read_initial(self, cmd, headers, body):
        assert cmd.lower() == 'connect', "Invalid cmd: expected CONNECT"
        self.state = 'connected'
        self.sendFrame('CONNECTED', {"session": self.id}, "")
        self.factory.connected(self)
        
    def read_connected(self, cmd, headers, body):
        return getattr(self, 'frame_%s' % cmd.lower())(headers, body)
    
    def frame_subscribe(self, headers, body):
        self.factory.subscribe(self, headers['destination'])
    
    def frame_unsubscribe(self, headers, body):
        self.factory.unsubscribe(self, headers['destination'])
    
    def frame_send(self, headers, body):
        self.factory.send(headers['destination'], body, headers)
    
    def frame_disconnect(self, headers, body):
        self.transport.loseConnection()
    
    def connectionLost(self, reason):
        self.factory.disconnected(self)
        
class Queue(object):
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.subscribers = []
        self.messages = []
            
    def subscribe(self, proto):
        if proto not in self.subscribers:
            self.subscribers.append(proto)
        while self.messages:
            message = self.messages.pop(0)
            self.send(*message)
            
    def unsubscribe(self, proto):
        if proto in self.subscribers:
            self.subscribers.remove(proto)
            
    def send(self, headers, body):
        if not self.subscribers:
            self.messages.append((headers, body))
        else:
            target = self.subscribers.pop(0)
            self.id += 1
            id = self.name + '_' + str(self.id)
            headers.update({'destination': self.name, 'message-id': id})
            target.sendFrame('MESSAGE', headers, body)
            self.subscribers.append(target)
    
    def empty(self):
        return not bool(self.subscribers or self.messages)
    
class Topic(object):
  
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.subscribers = []
            
    def subscribe(self, proto):      
        if proto not in self.subscribers:
            self.subscribers.append(proto)
            
    def unsubscribe(self, proto):
        if proto in self.subscribers:
            self.subscribers.remove(proto)

    def send(self, headers, body):
        self.id += 1
        id = self.name + '_' + str(self.id)
        headers.update({'destination': self.name, 'message-id': id})
        for target in self.subscribers:
            target.sendFrame('MESSAGE', headers, body)      

    def empty(self):
        return not bool(self.subscribers)

class StompFactory(Factory):
    protocol = StompProtocol
    
    def __init__(self):
        self.destinations = {}
        self.subscriptions = {}
        self.id = 0
        
    def subscribe(self, proto, name):
        if name not in self.destinations:
            if name.startswith('/queue/'):
                self.destinations[name] = Queue(name)
            else:
                self.destinations[name] = Topic(name)
        dest = self.destinations[name]
        dest.subscribe(proto)
        usersub = self.subscriptions[proto.id]
        if dest not in usersub:
            usersub.append(dest)
            
    def unsubscribe(self, proto, name):
        dest = self.destinations.get(name, None)
        if dest:
            dest.unsubscribe(proto)
            if dest.empty():
                del self.destinations[name]
        usersub = self.subscriptions[proto.id]
        if dest in usersub:
            usersub.remove(dest)
                            
    def connected(self, proto):
        self.subscriptions[proto.id] = []
        
    def disconnected(self, proto):
        for sub in self.subscriptions[proto.id]:
            sub.unsubscribe(proto)
        del self.subscriptions[proto.id]
    
    def send(self, dest_name, body, headers={}):
        dest = self.destinations.get(dest_name, None)
        if not dest and dest_name.startswith('/queue/'):
            dest = Queue(dest_name)
            self.destinations[dest_name] = dest        
        if dest:
            dest.send(headers, body)
        else:
            pass    


def setup(reactor, port, interface):
    """Create a listenTCP entry in the reactor, which
    if twisted is running will start the stomp broker
    handling client connections.
    
    :param reactor: twisted reactor.
    :param port: TCP port on which to listen.
    :param interface: The interface on which to bind.
    
    """
    reactor.listenTCP(port, StompFactory(), interface=interface)
            

def main(): 
    from optparse import OptionParser
    import sys
    parser = OptionParser()
    parser.add_option(
        "-p",
        "--port",
        dest="port",
        type="int",
        default=61613,
        help="listening port value"
    )
    parser.add_option(
        "-i",
        "--interface",
        dest="interface",
        type="string",
        default="",
        help="hostname the daemon should bind to (default: all interfaces)"
    )
    
    (options, args) = parser.parse_args(sys.argv)
    from twisted.internet import reactor
    setup(reactor, options.port, options.interface)
    print "Starting Morbid Stomp server @ stomp://" + options.interface+ ":" + str(options.port)
    reactor.run()
    
if __name__ == "__main__":
    main()