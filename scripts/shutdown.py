#!python 
"""
Connect to the proxydispatch on 1901 and issue a shutdown() call over xmlrpc.

The director will shut all parts down in an orderly fashion.

"""
import sys
import socket
from xmlrpclib import Server
from optparse import OptionParser



def main():
    """
    Connect to a directors proxy dispatch and send out a shutdown command.
    """
    
    parser = OptionParser()    

    parser.add_option("-u", "--uri", action="store", dest="uri", default="http://localhost:1901",
                      help="The uri of the director proxydispatch to connect to.")
    
    (options, args) = parser.parse_args()
    uri = options.uri
    s = Server(uri)
    
    try:
        s.shutdown()
        
    except socket.error, e:
        sys.stderr.write("Unable to connect on '%s' - %s\n" % (uri, str(e)))
        
    else:
        sys.stdout.write("Shutdown called on '%s' OK.\n" % (uri))


if __name__ == "__main__":
    main()

