"""
"""
import sys
import time
import uuid
import random
import urllib
import socket
import logging

import simplejson

from evasion.messenger import events
from evasion.messenger import eventutils
from evasion.messenger import xulcontrolprotocol
from evasion.director.tools.net import wait_for_service


class BrowserCallReplyTimeout(Exception):
    """Raised when the call callBrowserWaitReply() when the timeout for a reply occurs.
    """
    
class BrowserNotPresent(Exception):
    """Raised when the call callBrowserWaitReply() cannot connect to the browser/viewpoint
    control port.
    """


class DirectBrowserCalls(object):
    """This directly instructs the browser to act on instructions
    via its control port 7055 (default).
    
    """
    def __init__(self, port=7055, interface='127.0.0.1'):
        """Give the post an host we should talk too.
        """
        self.log = logging.getLogger("evasion.director.viewpointdirect.DirectBrowserCalls")
        self.port = 7055
        self.interface = '127.0.0.1'
        
        # validate and store what we've been given
        self.update(port, interface)


    def update(self, port, interface):
        """Update the direct browser communications details for a different location.
        
        port:
            This is the viewpoint TCP port (default: 7055)
        
        interface:
            This is the viewpoint interface (default: '127.0.0.1')
        
        """
        self.port = int(port)
        self.interface = interface


    def waitForReady(self, retries=0, retry_period=5.0):
        """Called to wait until the viewpoint interface is ready on the host and port.

        retries: (default: 0)
           The number of attempts before giving up on 
           connecting to the browser.
           
           If this is 0 then we will wait forever for 
           the browser to appear.
           
        retry_period: (default: 5.0)
           The amount of seconds to wait before the next
           connection attempt.

        returned:

            True: success
            Failed: failed to connect after maximum retries.
            
        """
        return wait_for_service(self.interface, int(self.port), retries, retry_period)

    
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
            raise BrowserNotPresent("Viewpoint/Browser Control COMMS Error")
            
        ##print "rc:",rc

        return rc

    
    def browserQuit(self, replyto='no-one'):
        """Called to recover where the browser is looking currently.
        """
        control_frame = {
            'command' : 'exit',
            'args' : {}
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("browserQuit: Sending command: %s " % str(d))
        rc = self.write(d)
        self.log.debug("browserQuit: rc %s" % str(rc))

        return rc

    
    def getBrowserUri(self, replyto='no-one'):
        """Called to recover where the browser is looking currently.
        """
        control_frame = {
            'command' : 'get_uri',
            'args' : {}
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        #self.log.debug("getBrowserUri: Sending command %s" % str(d))
        rc = self.write(d)
        #self.log.debug("getBrowserUri: rc %s" % str(rc))

        return rc

    
    def setBrowserUri(self, args, replyto='no-one'):
        """Called to tell the XUL Browser where to point
        """
        # Go to yahoo:
        control_frame = {
            'command' : 'set_uri',
            'args' : {'uri':args}
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("setBrowserUri: Sending command: %s " % str(d))
        rc = self.write(d)
        self.log.debug("setBrowserUri: rc %s " % str(rc))

        return rc

        
    def replaceContent(self, content_id, content, replyto='no-one'):
        """Called to replace content inside the viewpoint browser window with
        the given content fragment.
        """
        content=urllib.quote(content)
        control_frame = {
            'command' : 'replace',
            'args' : {'id' : content_id, 'content' : content}
        }
        d = dict(replyto=replyto, data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.debug("replaceContent: Sending command: %s " % str(d))
        rc = self.write(d)
        self.log.debug("replaceContent: rc %s " % str(rc))

        return rc
        

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

        self.log.debug("callFunction: Sending command: %s " % str(d))
        rc = self.write(d)
        self.log.debug("callFunction: rc %s " % str(rc))

        return rc

        
    def newSessionId(self):
        """Generate a sessionid for a callBrowserWaitReply.

        This is used to generate the reply_<...> call back
        and passed as the first argument to the javascript
        function.
        
        """
        return 'reply_%s' % str(uuid.uuid4())
    

    def callBrowserWaitReply(self, sessionid, call_str, timeout=180):
        """Call the browser and set up the callback handler on which
        we will receive the browser's response.

        call_str:
            This must be a valid javascript call in web page which
            viewpoint is currently displaying.

        timeout:
            The amount of seconds to wait before giving up on
            a response.

        Note:
            If no reponse is received within timeout seconds then
            a messenger.EventTimeout will be raised.
            
        """
        # Create the reply event and register it before. We do this before sending
        # the function call and reply event (session id) to the browser. This means
        # we won't miss the reponse if it happens quickly.
        #
        sessionid = simplejson.loads(sessionid)
        reply_event = events.EVT(sessionid)
        async_reply_catch = eventutils.Catcher(reply_event, timeout)        
        self.log.debug("callBrowserWithReply: creating reply signal for browser reply: '%s' " % sessionid)

        # Create the call to the browser:
        #
        self.log.debug("callBrowserWaitReply: invoking '%s' in the browser " % call_str)
        self.callFunction(call_str)
            
        # Now wait for the reply if it hasn't arrived already.
        #
        self.log.debug("callBrowserWaitReply: waiting for browser response '%s'." % sessionid)
        try:
            async_reply_catch.wait()
        except messenger.EventTimeout, e:
            raise BrowserCallReplyTimeout("No the reply '%s' was not received withing '%s' seconds." % (reply_event, timeout))
        
        self.log.debug("callBrowserWaitReply: response received '%s'." % async_reply_catch.event)

        return async_reply_catch.event
        
        
def main():
    """Command line interface to remote call
    """
    from evasion.director import utils
    from optparse import OptionParser

    utils.log_init(logging.DEBUG)
    log = logging.getLogger("evasion.director.viewpointdirect.main")
    
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
