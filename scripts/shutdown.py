#!python 
"""
Connect to the proxydispatch on 1901 and issue a shutdown() call over xmlrpc.

The director will shut all parts down in an orderly fashion.

"""
from xmlrpclib import Server
s = Server("http://localhost:1901").shutdown()
