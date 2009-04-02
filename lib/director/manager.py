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
        self.browserPort = '7055'
        self.browserHost = '127.0.0.1'


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
        xulbrowser_app = cfg.get('browser')

        # Spawn the xul browser using the new configuration:
        command = "%s %s -startport %s" % (xulrunner, xulbrowser_app, port)
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

        if part == "web":
            process = self.appProcess
            
        elif part == "device":
            process = self.deviceMainProcess
            
        elif part == "broker":
            process = self.brokerProcess
            
        else:
            # xul browser is the default:
            process = self.browserProcess

        if process and process.poll() is None:
            returned = True

        return returned


    def waitForReady(self, port):
        """Called to wait for the web presence to respond to
        normal get requests, then the browser can be started.
        """
        URI = "http://localhost:%s" % port
        
        # copy the value and not the reference:
        retries = copy.deepcopy(self.PORT_RETRIES)

        while retries:
            self.log.info("waitForReady: (reties left:%d) check if we can get <%s>." % (retries, URI))
            retries -= 1
            try:
                urllib.urlopen(URI)
                # success, its ready.
                break;
            except IOError, e:
                # Not ready yet. I should check the exception to
                # make sure its socket error or we could be looping
                # forever. I'll need to use a state machine if this
                # prototype works. For now I'm taking the "head in
                # the sand" approach.
                pass
            
            time.sleep(0.8)


    def write(self, data, port, host, RECV=2048):
        """Do a socket send and wait to receive directly to the xul browser.

        This side steps the broker if its not running already.
        
        """
        rc = ''
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            s.send(data)
            rc = s.recv(RECV)
            s.close()
        except socket.error, e:
            self.log.exception("write: socket send error - ")

        return rc


    def setBrowserUri(self, uri, port, host='127.0.0.1'):
        """Called to tell the XUL Browser where to point
        """
        # Go to yahoo:
        control_frame = {
            'command' : 'set_uri',
            'args' : {'uri':uri}
        }
        d = dict(replyto='no-one', data=control_frame)
        d = xulcontrolprotocol.dump(d)

        self.log.info("setBrowserUri: Sending set uri command:\n%s\n\n" % str(d))
        rc = self.write(d, port, host)
        self.log.info("setBrowserUri:\n%s\n\n" % str(rc))
        

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

        self.log.info("appmain: Running.")


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
            self.log.warn("main: the XulBrowser has been DISABLED in the configuration by the user.")
            
        disable_deviceaccess = cfg.get('disable_deviceaccess', "no")
        if disable_deviceaccess != "no":
            self.log.warn("main: the deviceaccess has been DISABLED in the configuration by the user.")
        
        
        self.log.info("appmain: Running.")
        while not isExit():

            # Maintain the stomp broker, if its not disabled:
            if disable_broker == "no" and not self.isRunning('broker'):
                self.log.info("main: restarting broker.")
                self.startBroker()

            # Maintain the hardware abstraction layer, if its not disabled:
            if disable_deviceaccess == "no" and not self.isRunning('device'):
                self.log.info("main: restarting device layer.")
                self.startdeviceaccess()
                
            # Maintain the XUL Browser if its not disabled:
            if disable_xul == "no" and not self.isRunning('browser'):
                # No, we must start the XUL Browser.
                self.browserPort = self.getFreePort()
                messenger.xulcontrolprotocol.setup(dict(host=self.browserHost, port=self.browserPort))

                # Recover the file system uri we'll give to browser startup.
                from pkg_resources import resource_filename
                filename = resource_filename(director.xulbrowserpage.__name__, 'index.html')
                start_url = filename.replace('\\','/')
                self.log.warn("main: recovered xul browser index starturl '%s'." % start_url)
                self.startBrowser(self.browserPort, start_url)

                if self.isRunning('web'):
                    # Redirect the xul browser at the web presence:
                    self.waitForReady(self.appPort)
                    self.setBrowserUri("http://%s:%s" % (self.appHost, self.appPort), self.browserPort)
                

            # Maintain the web presence, if its not disabled:
            if disable_app == "no" and not self.isRunning('web'):
                # Get a random free port to run the web presence on and use this
                # to point the XUL browser at it initially. If the fix_port option
                # is present in the configuration then the user wants us to always
                # use a specific port.
                #
                fix_port = cfg.get('fix_port', None)
                if fix_port:
                    self.appPort = fix_port # Start the web presence on the same port.
                    self.log.warn("main: the user has fixed the port (%s) that the web presence and browser will use in configuration." % fix_port)
                else:
                    self.appPort = self.getFreePort()

                # Start the web presence on this port and then make sure its
                # ready for requests, before starting the browser:
                self.startapp(self.appPort)
                while not self.isRunning('web'):
                    self.log.info("main: waiting for web presence to start")
                    time.sleep(2)

                self.waitForReady(self.appPort)

                # Ok, redirect the xul browser at the web presence:
                self.setBrowserUri("http://%s:%s" % (self.appHost, self.appPort), self.browserPort)

                
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
        cfg = director.config.get_cfg()

        # Set up the messenger protocols where using:        
        messenger.stompprotocol.setup(dict(
            host=cfg.get('msg_host'),
            port=int(cfg.get('msg_port')),
            username=cfg.get('msg_username'),
            password=cfg.get('msg_password'),
            channel=cfg.get('msg_channel'),
        ))


        # Set up the default messenger protocols we are using:        
        messenger.xulcontrolprotocol.setup(
            dict(host="localhost", port=7055)
        )

        try:
            self.log.info("main: Running.")
            messenger.run(self.appmain)
        finally:
            self.log.info("main: shutdown!")
            self.kill()
            self.exit()
            

