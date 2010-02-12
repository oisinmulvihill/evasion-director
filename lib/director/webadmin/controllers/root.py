import logging

from routes import url_for
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from director.signals import SignalsSender
from webadmin.lib.base import BaseController, render




class RootController(BaseController):

    def __init__(self, *args, **kw):
        BaseController.__init__(self, *args, **kw)
        self.log = logging.getLogger('webadmin.controllers.root.RootController')
        self.director = SignalsSender()
        

    def index(self):
        
        # Check if the director is present
        self.director.ping()
    
        c.modules = self.director.webadminModules()
    
        return render('/root.mako')


    def login(self):
        """This is where the login form should be rendered.
        """
        # Without the login counter, we won't be able to tell if the user has
        # tried to log in with the wrong credentials
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            print('Wrong credentials')
            
        c.login_counter = 0 #login_counter
        c.url_for = url_for
        c.came_from = request.params.get('came_from') or url_for('/')
        
        return render('login.mako')     
