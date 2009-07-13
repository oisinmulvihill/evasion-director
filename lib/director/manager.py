"""
This class handles the running and management of both the XUL
Browser and the evasion web presence.

Created by Oisin Mulvihill on 2007-05-18.

"""
import os
import time
import copy
import urllib
import random
import socket
import os.path
import logging
import StringIO
import simplejson
import subprocess

import agency
import director
import messenger
import director.config
from director import proxydispatch
from director import viewpointdirect
from messenger import xulcontrolprotocol


def get_log():
    return logging.getLogger("director.manager")


class Manager(object):
    """Manage the running of both the XUL Browser and Web Presence services.
    """
    PORT_RETRIES = 40
    
    def __init__(self):
        """
        """
        self.log = logging.getLogger("director.manager.Manager")
        self.browserProcess = None
        self.appProcess = None
        self.agencyMainProcess = None
        self.brokerProcess = None
        self.appPort = '9808'
        self.appHost = '127.0.0.1'

        self.startURI = "http://%s:%s" % (self.appHost, self.appPort)

        # The viewpoint access details:
        self.browserPort = '7055'
        self.browserHost = '127.0.0.1'        
        self.viewpoint = viewpointdirect.DirectBrowserCalls(self.browserPort, self.browserHost)
        self.viewpointUp = False
        
        # True is the app has been start or restarted. If this is the case
        # then the browser should be repointed at the running appl
        self.appRestarted = False

        # Used in case we need to run another app in addtion to current set.
        self.optionalAppProcess = None
        self.optionalAppStarted = False


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


    def winKill(self, cmd):
        """Attempt to call taskkill.exe to clean up any old xulrunner instance.
        This will only work on winxp. The more correct approach would be to
        re use an existing xul browser. It should actuall check if xul is up
        and on the port. I could then instruct it where to go to.
        
        """
        cmd = "taskkill.exe /F /T /IM %s " % cmd
        try:
            retcode = subprocess.call(cmd, shell=True)
            self.log.info("winKill: taskkill return code <%s>" % retcode)
        except OSError, e:
            self.log.warn("winKill: didn't run <%s> Not on winxp?" % str(e))


    def winKillPID(self, pid):
        """Attempt to call taskkill.exe to clean up any old xulrunner instance.
        This will only work on winxp. The more correct approach would be to
        re use an existing xul browser. It should actuall check if xul is up
        and on the port. I could then instruct it where to go to.
        
        """
        cmd = "taskkill.exe /F /T /PID %s " % pid
        try:
            retcode = subprocess.call(cmd, shell=True)
            self.log.info("winKillPID: taskkill return code <%s>" % retcode)
        except OSError, e:
            self.log.warn("winKillPID: didn't run <%s> Not on winxp?" % str(e))


    def startBroker(self):
        """Called to spawn the MorbidQ broker as a process.

        """
        self.winKill('morbidsvr')
        
        cfg = director.config.get_cfg()
        app = cfg.get('brokermain')
        app_dir = cfg.get('brokermaindir', '')
        self.log.debug("startBroker: app dir '%s'." % app_dir)
        
        if not os.path.isdir(app_dir):
            raise ValueError("The directory to run from '%s' does not exist!" % app_dir)

        command = app
        self.log.debug("startBroker: running <%s>" % command)

        self.brokerProcess = subprocess.Popen(
                args = command,
                shell=True,
                cwd=app_dir,
                )
        pid = self.brokerProcess.pid
        return pid


    def startBrowser(self, port, url=None):
        """Called to spawn the xul browser as process.

        This is a two step process:

           1. Update the pref.js with the new URI of the
           web presence.

           2. Then spawn the xul browser.

        """
        self.winKill('xulrunner.exe')

        cfg = director.config.get_cfg()
        xulrunner = cfg.get('xulrunner')
        viewpoint_app = cfg.get('browser')

        # Spawn the xul browser using the new configuration:
        command = "%s %s -startport %s" % (xulrunner, viewpoint_app, port)
        if url:
            # Quote it " to spaces don't throw us if they are in the
            # path name given for the start up index.
            command = '%s -starturi "file:///%s" ' % (command, url)
        self.log.debug("startBrowser: spawning <%s>" % command)

        self.browserProcess = subprocess.Popen(
                args = command,
                shell=True,
                )
        pid = self.browserProcess.pid

        self.log.debug("startBrowser: done.")
        return pid


    def startOptionalApp(self):
        """Called to spawn another program if the configuration is present for
        app2 is present.
        """
        cfg = director.config.get_cfg()
        app = cfg.get('app2')
        app_dir = cfg.get('app2_dir','')

        if not app_dir:
            self.log.error("The app2 command is empty!")
            return

        if not os.path.isdir(app_dir):
            self.log.error("The app2 directory to run from '%s' does not exist!" % app_dir)
            return

        command = "%s" % (app)
        self.log.debug("startOptionalApp: running <%s>" % command)

        self.optionalAppProcess = subprocess.Popen(
                args = command,
                shell=True,
                cwd=app_dir,
                )
        pid = self.optionalAppProcess.pid

        self.log.debug("startOptionalApp: done.")
        
        return pid


    def startApp(self, port):
        """Called to spawn the web app as process on the given port.
        """
        cfg = director.config.get_cfg()
        app = cfg.get('app')
        app_dir = cfg.get('app_dir')

        if not os.path.isdir(app_dir):
            raise ValueError("The app directory to run from '%s' does not exist!" % app_dir)

        command = "%s" % (app)
        self.log.debug("startApp: running <%s>" % command)

        self.appProcess = subprocess.Popen(
                args = command,
                shell=True,
                cwd=app_dir,
                )
        pid = self.appProcess.pid
        
        return pid


    def startAgency(self):
        """Called to spawn the Agency process.
        """
        cfg = director.config.get_cfg()
        agency = cfg.get('agency')
        agencydir = cfg.get('agencydir')

        if not os.path.isdir(agencydir):
            raise ValueError("The Agency directory to run from '%s' does not exist!" % agencydir)

        self.log.debug("startAgency: running <%s> from <%s>" % (agency, agencydir))

        self.agencyMainProcess = subprocess.Popen(
                args = agency,
                shell=True,
                cwd=agencydir,
                )
        pid = self.agencyMainProcess.pid
        
        return pid


    def isRunning(self, part):
        """Called to test the web presence or browser is running.

        part:
            'web' | 'browser' | 'agency' | 'broker'

            Note : if the part isn't one of these the
            ValueError will be raised.

        returned:
            True - its running.
            False - its not running.
            
        """
        returned = False

        # Prevent multiple process spawns if the part is specified wrongly.
        if part not in ['web','browser', 'agency', 'broker','app2']:
            raise ValueError, "Unknown part <%s> to check." % part

        def check(proc):
            # Check the proccess is running:
            returned = False
            if proc and proc.poll() is None:
                returned = True
            return returned

        if part == "web":
            returned = check(self.appProcess)
                    
        elif part == "agency":
            returned = check(self.agencyMainProcess)
            
        elif part == "broker":
            returned = check(self.brokerProcess)
            
        elif part == "app2":
            returned = check(self.optionalAppProcess)
            
        else:
            # check if the managed xul browser running:
            returned = check(self.browserProcess)
            if not returned:
                # Just check if its running outside of the director
                # i.e. I can connect to its command interface. If
                # so its considered as running and should be repointed
                # at the web app if it needs to be.
                returned = self.viewpoint.waitForReady(retries=1)                

        return returned


    def waitForReady(self, port):
        """Called to wait for the web presence to respond to
        normal get requests, then the browser can be started.
        
        returned:
            True: success web app ready.
        
        """
        returned = False
        URI = "http://localhost:%s" % port
        
        # copy the value and not the reference:
        retries = copy.deepcopy(self.PORT_RETRIES)

        while retries:
            self.log.info("waitForReady: (reties left:%d) check if we can get <%s>." % (retries, URI))
            retries -= 1
            try:
                urllib.urlopen(URI)
            except IOError, e:
                # Not ready yet. I should check the exception to
                # make sure its socket error or we could be looping
                # forever. I'll need to use a state machine if this
                # prototype works. For now I'm taking the "head in
                # the sand" approach.
                pass
            else:
                # success, its ready.
                returned = True
                break;
            
            time.sleep(0.8)
            
        return returned


    def appmain(self, isExit):
        """I need to implement a state machine to do this properly...

        isExit:
            This is a function that will return true
            when its time to exit.


        Note: this is a thread which we are running in and the
        messenger will determine when its time to exit.
        
        """
        import director.config
        
        cfg = director.config.get_cfg()
        poll_time = float(cfg.get('poll_time'))

        # Recover the options to disable/enable the various parts:
        #
        disable_app = cfg.get('disable_app', "no")
        if disable_app != "no":
            self.log.warn("main: the Web Presence has been DISABLED in configuration.")

        disable_app2 = cfg.get('disable_app2', "no")
        if disable_app2 != "no":
            self.log.warn("main: the optional app has been DISABLED in configuration.")

        disable_broker = cfg.get('disable_broker', "no")
        if disable_broker != "no":
            self.log.warn("main: the Broker has been DISABLED in configuration.")

        disable_xul = cfg.get('disable_xul', "no")
        if disable_xul != "no":
            self.log.warn("main: the viewpoint has been DISABLED in the configuration by the user.")
            
        disable_agency = cfg.get('disable_agency', "no")
        if disable_agency != "no":
            self.log.warn("main: the Agency has been DISABLED in the configuration by the user.")

        # Register messenger hook for kill()
        def signal_exit(signal, sender, **data) :
            self.log.warn("main: signal_exit called")
            self.exit()
        dispatcher.connect(
          signal_exit,
          signal=messenger.EVT("EXIT_ALL")
        )

        def start_broker():
            self.log.info("main: starting broker.")
            print "start agencys"
            self.startBroker()
                    
        def start_app():
            # Start the app and wait for it to be ready:
            self.appPort = cfg.get('fix_port', 5000)
            self.startURI = "http://%s:%s" % (self.appHost, self.appPort)
            self.log.warn("main: [director] fix_port = %s " % self.appPort)
            self.startApp(self.appPort)
            while not self.isRunning('web'):
                self.log.info("main: waiting for web app to start")
                time.sleep(2)
            active = False
            while not active:
                self.log.info("main: waiting for web app to respond to requests")
                active = self.waitForReady(self.appPort)
            self.appRestarted = True
            
        def start_viewpoint():
            # Set up the xulcontrolprotocol point at the right direction:
            self.browserPort = 7055
            messenger.xulcontrolprotocol.setup(dict(host='127.0.0.1', port=self.browserPort))
            # Start viewpoint and wait until its ready.
            self.log.info("main: starting viewpoint...")
            self.startBrowser(self.browserPort)
            
        def repoint_viewpoint():
            # Point the viewpoint at the app.
            self.log.info("main: waiting for web app to be ready for connections.")
            result = self.waitForReady(self.appPort)
            if result:
                # Point viewpoint at the web app's uri:
                self.log.info("main: point viewpoint at web app.")
                self.viewpoint.setBrowserUri(self.startURI) 
        
                
        self.log.info("appmain: Running.")
        while not isExit():            
            # Maintain the stomp broker, if its not disabled:
            if disable_broker == "no" and not self.isRunning('broker'):
                start_broker()

            # Maintain the Agency manager, if its not disabled:
            if disable_agency == "no" and not self.isRunning('agency'):
                self.log.info("main: restarting agency layer.")
                self.startAgency()

            # Maintain the web application, if its not disabled:
            if disable_app == "no" and not self.isRunning('web'):
                # start and wait for it to be ready. This should
                # set the self.appRestarted to True. This will 
                # cause the xul browser to be repointed at the app. 
                start_app()

            # Maintain the web application, if its not disabled:
            if disable_app2 == "no" and not self.isRunning('app2'):
                self.startOptionalApp()

            # Check if viewpoint interface is up. This could mean the
            # user has started viewpoint outside of the manager. Point
            # It at the webapp if its running.
            #
            if self.isRunning('browser'):
                # Check its looking at the web app:
                self.viewpointUp = True
                if self.isRunning('web'):
                    try:
                        data = self.viewpoint.getBrowserUri()
                    except socket.error, e:
                        self.viewpointUp = False
                    else:
                        # no data is socket close.
                        if data:
                            rc = simplejson.loads(data)
                            uri = rc['data']
                            if not uri.startswith(self.startURI):
                                # Were not looking at app. Repointing...
                                self.log.error("main: viewpoint is not look at base URI '%s'! Repointing..." % self.startURI)            
                                repoint_viewpoint()
            else:
                if self.viewpointUp:
                    self.log.error("main: viewpoint interface went down!")            
                self.viewpointUp = False

            # Maintain the viewpoint process if its not disabled:
            if disable_xul == "no" and not self.isRunning('browser'):
                # Start it and wait for it to be ready:
                print "viewpoint starting"
                start_viewpoint()
                print "viewpoint started ok"

            # Don't busy wait if nothing needs doing:
            time.sleep(poll_time)

        self.log.info("appmain: Finished.")
            

    def exit(self):
        """Called by the windows service to stop the director service and
        all its children.
        
        """
        self.log.warn("exit: the director is shutting down.")
        messenger.quit()
        time.sleep(2)


    def kill(self):
        """Shutdown any remaining services with winKill()
        """
        if self.isRunning('browser'):
            self.log.warn("kill: STOPPING BROWSER.")
            if self.browserProcess:
                self.winKillPID(self.browserProcess.pid)
                self.winKill('xulrunner.exe')

        if self.isRunning('agency'):
            self.log.warn("kill: STOPPING Agency.")
            if self.agencyMainProcess:
                self.winKillPID(self.agencyMainProcess.pid)

        if self.isRunning('broker'):
            self.log.warn("kill: STOPPING BROKER.")
            if self.brokerProcess:
                self.winKillPID(self.brokerProcess.pid)
                self.winKill('morbidsvr')

        if self.isRunning('web'):
            self.log.warn("kill: STOPPING WEB APP.")
            if self.appProcess:
                self.winKillPID(self.appProcess.pid)

        if self.isRunning('app2'):
            self.log.warn("kill: STOPPING OPTIONAL APP.")
            if self.appProcess:
                self.winKillPID(self.optionalAppProcess.pid)


                
    def main(self):
        """Set up the agency layer and then start the messenger
        layer running with the app main.
        
        """
        self.log.info("main: setting up stomp connection.")        

        cfg = director.config.get_cfg()
        
        # Set up the messenger protocols where using:        
        self.log.info("main: setting up stomp connection to broker.")
        messenger.stompprotocol.setup(dict(
            host=cfg.get('msg_host'),
            port=int(cfg.get('msg_port')),
            username=cfg.get('msg_username'),
            password=cfg.get('msg_password'),
            channel=cfg.get('msg_channel'),
        ))
        
        port = int(cfg.get('proxy_dispatch_port', 1901))
        self.log.info("main: setting up reply proxy dispatch http://127.0.0.1:%s/ ." % port)
        proxydispatch.setup(port)

        try:
            self.log.info("main: Running.")
            messenger.run(self.appmain)
        finally:
            self.log.info("main: shutdown!")
            self.kill()
            self.exit()
            

