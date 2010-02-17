"""

"""
import static
import templates
import controllers

def configure(map):
    """
    """
    import os
    import os.path
    
    # Work out where the files are on disk:
    #
    controllers_dir = os.path.abspath(controllers.__path__[0])
    static_dir = os.path.abspath(static.__path__[0])
    templates_dir = os.path.abspath(templates.__path__[0])
    
    # Set up the routing for our URLs
    #
    base = 'webadmin.controllers.%s'
    
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller=base % 'error')
    map.connect('/error/{action}/{id}', controller=base % 'error')
    
    # Root site:
    map.connect('root', '/', controller=base % 'root', action='index')
    map.connect('login', '/login', controller=base % 'root', action='login')
    
#    map.connect('/{controller}/{action}')
#    map.connect('/{controller}/{action}/{id}')

    return dict(
        controllers = controllers_dir,
        static = static_dir,
        templates = templates_dir,
        map = map,
    )
    
