"""
"""
import time

import messenger


class MessengerWrapper(object):

    def __init__(self, test, testfunc) :
        self.error = None
        self.test = test
        self.testfunc = testfunc
        
    def main(self, isExit):
        try:
            # Need this little sleep in to wait for the messenger to connect
            time.sleep(5)
            # Run the actual tests now that messenger is up and running:
            self.testfunc(self.test)
        except Exception, e:
            # Capture the exception to raise it in the main thread.
            self.error = sys.exc_info()
        # Exit cleanly no matter what.
        messenger.quit()


def runWith(test, func, cfg = messenger.default_config['stomp']):
    """Runs a test with the messaging system active.
    
    test: test case object
    func: function that is your test, will be run with the test object as first argument
    cfg : Messenger config dict
    
    """
    wrap = MessengerWrapper(test,func)
    messenger.stompprotocol.setup(cfg)
    messenger.run(wrap.main)
    
    if wrap.error:
        # not all error work with raise and a quick fix it to print the error as a string.
        get_log().error("runWith - wrap.error: %s " % str(wrap.error))
        
        # Re-raise the exception from the thread:
        raise wrap.error[0](str(wrap.error[1])+ "".join(traceback.format_tb(wrap.error[2])))

