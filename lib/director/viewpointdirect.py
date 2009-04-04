"""
"""
import sys
import random
import urllib
import socket
import logging

from messenger import xulcontrolprotocol


class DirectBrowserCalls(object):
    """This directly instructs the browser to act on instructions
    via its control port 7055 (default).
    
    """
    def __init__(self, port=7055, interface='127.0.0.1'):
        """Give the post an host we should talk too.
        """
        self.log = logging.getLogger("director.viewpointdirect.DirectBrowserCalls")
        self.port = int(port)
        self.interface = interface


    def getFreePort(self):
        """Called to return a free TCP port that we can use.

        This function gets a random port between 2000 - 40000.
        A test is done to check if the port is free by attempting
        to use it. If its not free another port is checked
        
        """
        # copy the value and not the reference:
        retries = copy.deepcopy(self.PORT_RETRIES)

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
                self.log.info("getFreePort: port not free %s, retrying." % free_port)
                
        if not free_port:
            raise ManagerError, "I can't get a free port and I've tried %s times." % PORT_RETRIES

        self.log.info("getFreePort: Free Port %s." % free_port)

        return free_port

    
    def write(self, data, RECV=2048):
        """Do a socket send and wait to receive directly to the xul browser.

        This side steps the broker if its not running already.
        
        """
        rc = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.interface, int(self.port)))
            s.send(data)
            rc = s.recv(RECV)
            s.close()
            
        except socket.error, e:
            self.log.error("write: socket send error - Is browser running? ")

        return rc

    
    def browserQuit(self):
        """Called to recover where the browser is looking currently.
        """
        control_frame = {
            'command' : 'exit',
            'args' : {}
        }
        d = dict(replyto='no-one', data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("browserQuit: Sending command:\n%s\n\n" % str(d))
        rc = self.write(d)
        self.log.debug("browserQuit:\nrc: %s\n\n" % str(rc))

    
    def getBrowserUri(self, replyto='no-one'):
        """Called to recover where the browser is looking currently.
        """
        control_frame = {
            'command' : 'get_uri',
            'args' : {}
        }
        d = dict(replyto='no-one', data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("getBrowserUri: Sending command:\n%s\n\n" % str(d))
        rc = self.write(d)
        self.log.debug("getBrowserUri:\nrc: %s\n\n" % str(rc))

    
    def setBrowserUri(self, args, replyto='no-one', host='127.0.0.1'):
        """Called to tell the XUL Browser where to point
        """
        # Go to yahoo:
        control_frame = {
            'command' : 'set_uri',
            'args' : {'uri':args}
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("setBrowserUri: Sending command:\n%s\n\n" % str(d))
        rc = self.write(d)
        self.log.debug("setBrowserUri:\n%s\n\n" % str(rc))


    def callFunction(self, args, replyto='no-one'):
        """Call a javascript function in the browser.
        """        
        control_frame = {
            'command' : 'call',
            'args' : {
                'call':args, 
            }
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("callFunction: Sending command:\n%s\n\n" % str(d))
        rc = self.write(d)
        self.log.debug("callFunction:\n%s\n\n" % str(rc))
        
        
def main():
    """Command line interface to remote call
    """
    from director import utils
    from optparse import OptionParser

    utils.log_init(logging.DEBUG)
    log = logging.getLogger("")
    
    parser = OptionParser()

    parser.add_option(
        "-c","--command", action="store", dest="cmd",
        default='get_uri',
        help="Command to use. Default: get_uri"
    )
    parser.add_option(
        "-a","--args", action="store", dest="args",
        default='',
        help="The comm port the browser is using. Default: Nothing"
    )
    parser.add_option(
        "-p", "--port", action="store", dest="port",
        default=7055,
        help="The comm port the browser is using. Default: 7055"
    )
    parser.add_option(
        "-i", "--host", action="store", dest="host",
        default='127.0.0.1',
        help="The comm interface the browser is listening on. Default: 127.0.0.1"
    )
    
    (options, args) = parser.parse_args()

    b = DirectBrowserCalls(port=options.port, interface=options.host)

    log.info("Running command '%s' with args '%s'." % (options.cmd, options.args))
    
    if options.cmd == 'get_uri':
        b.getBrowserUri()

    elif options.cmd == 'set_uri':
        b.setBrowserUri(options.args)

    elif options.cmd == 'call':
        b.callFunction(options.args)

    elif options.cmd == 'exit':
        b.browserQuit()

    else:
        msg = "Unknown command '%s'." % options.cmd
        log.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)

    sys.exit(0)
        

if __name__ == "__main__":
    main()
