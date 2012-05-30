"""
"""
import json

from evasion.agency.agents.base.service import WebServerAgent


class Agent(WebServerAgent):
    """This runs a

        [rest_test]
        #disabled = 'yes'
        cat = service
        agent = evasion.agency.agents.testing.resttest

        # Where to to bind the server to:
        interface = 0.0.0.0
        port = 39475


    The methods do_GET, do_POST, do_PUT and do_DELETE can be overridden
    to handle REST method actions in derived agents.

    """
    def returned(self, request_handler, method):
        return json

    def do_GET(self, request_handler):
        """Handle a GET request, override to implement.
        """
        super(Agent.self).do_GET(request_handler)

    def do_POST(self, request_handler):
        """Handle a GET request, override to implement.
        """
        super(Agent.self).do_GET(request_handler)

    def do_PUT(self, request_handler):
        """Handle a PUT request, override to implement.
        """
        super(Agent.self).do_GET(request_handler)

    def do_DELETE(self, request_handler):
        """Handle a DELETE request, override to implement.
        """
        super(Agent.self).do_GET(request_handler)
