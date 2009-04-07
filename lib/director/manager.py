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
import subprocess

import director
import messenger
import deviceaccess
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
        self.deviceMainProcess = None
        self.brokerProcess = None
        self.appPort = '9808'
        self.appHost = '127.0.0.1'
        
        # The viewpoint access details:
        self.browserPort = '7055'
        self.browserHost = '127.0.0.1'        
        self.viewpoint = viewpointdirect.DirectBrowserCalls(self.browserPort, self.browserHost)
        
        # True is the app has been start or restarted. If this is the case
        # then the browser should be repointed at the running appl
        self.appRestarted = False


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


    def startapp(self, port):
        """Called to spawn the web presence as process on the given port.
        """
        cfg = director.config.get_cfg()
        app = cfg.get('app')
        app_dir = cfg.get('app_dir')

        if not os.path.isdir(app_dir):
            raise ValueError("The app directory to run from '%s' does not exist!" % app_dir)

        command = "%s" % (app)
        self.log.debug("startapp: running <%s>" % command)

        self.appProcess = subprocess.Popen(
                args = command,
                shell=True,
                cwd=app_dir,
                )
        pid = self.appProcess.pid
        
        return pid


    def startdeviceaccess(self):
        """Called to spawn the deviceaccess process.
        """
        cfg = director.config.get_cfg()
        devicemain = cfg.get('devicemain')
        devicemaindir = cfg.get('devicemaindir')

        if not os.path.isdir(devicemaindir):
            raise ValueError("The deviceaccess directory to run from '%s' does not exist!" % devicemaindir)

        self.log.debug("startdeviceaccess: running <%s> from <%s>" % (devicemain, devicemaindir))

        self.deviceMainProcess = subprocess.Popen(
                args = devicemain,
                shell=True,
                cwd=devicemaindir,
                )
        pid = self.deviceMainProcess.pid
        
        return pid


    def isRunning(self, part):
        """Called to test the web presence or browser is running.

        part:
            'web' | 'browser' | 'device' | 'broker'

            Note : if the part isn't one of these the
            ValueError will be raised.

        returned:
            True - its running.
            False - its not running.
            
        """
        returned = False

        # Prevent multiple process spawns if the part is specified wrongly.
        if part not in ['web','browser', 'device', 'broker']:
            raise ValueError, "Unknown part <%s> to check." % part

        def check(proc):
            # Check the proccess is running:
            returned = False
            if proc and proc.poll() is None:
                returned = True
            return returned

        if part == "web":
            returned = check(self.appProcess)
                    
        elif part == "device":
            returned = check(self.deviceMainProcess)
            
        elif part == "broker":
            returned = check(self.brokerProcess)
            
        else:
            # xul browser is the default:
            returned = check(self.browserProcess)
            if not returned:
                # Just check if its actually running outside of the
                # director i.e. I can connect to its command interface.
                returned = self.viewpoint.waitForReady(retries=30)                

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

        disable_broker = cfg.get('disable_broker', "no")
        if disable_broker != "no":
            self.log.warn("main: the Broker has been DISABLED in configuration.")

        disable_xul = cfg.get('disable_xul', "no")
        if disable_xul != "no":
            self.log.warn("main: the viewpoint has been DISABLED in the configuration by the user.")
            
        disable_deviceaccess = cfg.get('disable_deviceaccess', "no")
        if disable_deviceaccess != "no":
            self.log.warn("main: the deviceaccess has been DISABLED in the configuration by the user.")


        def start_broker():
            cfg = director.config.get_cfg()

            # Set up the messenger protocols where using:        
            messenger.stompprotocol.setup(dict(
                host=cfg.get('msg_host'),
                port=int(cfg.get('msg_port')),
                username=cfg.get('msg_username'),
                password=cfg.get('msg_password'),
                channel=cfg.get('msg_channel'),
            ))
            proxydispatch.setup(1901)
            
            self.log.info("main: restarting broker.")
            print "start devices"
            self.startBroker()
        

        def start_app():
            # Start the app and wait for it to be ready:
            self.appPort = cfg.get('fix_port', 5000)
            self.log.warn("main: [director] fix_port = %s " % self.appPort)
            self.startapp(self.appPort)
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
            # Wait for it to be ready:
            self.log.info("main: waiting for viewpoint readiness...")
            return self.viewpoint.waitForReady()
            
        def repoint_viewpoint():
            # Point the viewpoint at the app.
            self.log.info("main: waiting for web app to be ready for connections.")
            starturi = "http://%s:%s" % (self.appHost, self.appPort)
            result = self.waitForReady(self.appPort)
            if result:
                # Point viewpoint at the web app's uri:
                self.log.info("main: point viewpoint at web app.")
                self.viewpoint.setBrowserUri(starturi) 
        
                
        self.viewpointUp = True
        self.repointed = False
                
        self.log.info("appmain: Running.")
        while not isExit():
            print 1
            # Maintain the stomp broker, if its not disabled:
            if disable_broker == "no" and not self.isRunning('broker'):
                print "start broker"
                start_broker()
                
            print 2
            # Maintain the deviceaccess manager, if its not disabled:
            if disable_deviceaccess == "no" and not self.isRunning('device'):
                self.log.info("main: restarting device layer.")
                print "start devices"
                self.startdeviceaccess()

            print 3
            # Maintain the web application, if its not disabled:
            if disable_app == "no" and not self.isRunning('web'):
                # start and wait for it to be ready. This should
                # set the self.appRestarted to True. This will 
                # cause the xul browser to be repointed at the app. 
                print "start app"
                start_app()

            # Check if viewpoint interface is up:
            if self.viewpoint.waitForReady(retries=1):
                print "viewpoint up"
                self.viewpointUp = True
            else:
                print "viewpoint down"
                self.viewpointUp = False
                self.repointed = False


            # If the web app has been restarted redirect viewpoint at it:
            if self.viewpointUp and self.isRunning('web'):
                print 4.1
                if not self.repointed:
                    print "repointing"
                    repoint_viewpoint()
                    self.repointed = True
                print 4.2
                self.appRestarted = False


            # Maintain the XUL Browser if its not disabled:
            if disable_xul == "no" and not self.isRunning('browser'):
                # Start it and wait for it to be ready:
                start_viewpoint()                    
                # Point it at the web app:
                if result and self.isRunning('web'):
                    repoint_viewpoint()                                           
                else:
                    self.log.error("main: browser failed to start. Retrying...")            

            print 6
            # Don't busy wait if nothing needs doing:
            time.sleep(poll_time)
            print("appmain: tick")

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
            self.winKillPID(self.browserProcess.pid)
            self.winKill('xulrunner.exe')

        if self.isRunning('device'):
            self.log.warn("kill: STOPPING deviceaccess.")
            self.winKillPID(self.deviceMainProcess.pid)

        if self.isRunning('broker'):
            self.log.warn("kill: STOPPING BROKER.")
            self.winKillPID(self.brokerProcess.pid)
            self.winKill('morbidsvr')

        if self.isRunning('web'):
            self.log.warn("kill: STOPPING WEB PRESENCE.")
            self.winKillPID(self.appProcess.pid)


                
    def main(self):
        """Set up the device layer and then start the messenger
        layer running with the app main.
        
        """
        self.log.info("main: setting up stomp connection.")        
        try:
            self.log.info("main: Running.")
            messenger.run(self.appmain)
        finally:
            self.log.info("main: shutdown!")
            self.kill()
            self.exit()
            

