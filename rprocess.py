import sys, os, time
from multiprocessing import Process, Pipe
import rpy2.robjects as robs
import rpy2.rinterface as rint
from threading import Timer
from PyQt4.QtCore import QObject, SIGNAL

class OutputCatcher:
    def __init__(self, pipe):
        self.pipe = pipe

    def write(self, stuff):
        self.pipe.send(stuff)
#        sys.__stdout__.write(stuff)

    def flush(self):
        pass

    def clear(self):
        pass

class RProcess(Process):
    def __init__(self, pipe):
        Process.__init__(self)
        self.pipe = pipe

    def run(self):
        sys.stdout = sys.stderr = OutputCatcher(self.pipe)
        try_ = robs.r.get("try", mode='function')
        parse_ = robs.r.get("parse", mode='function')
        paste_ = robs.r.get("paste", mode='function')
        withVisible_ = robs.r.get("withVisible", mode='function')
        self.t = Timer(0.03, self.update)
        self.t.start()
        while 1:
            cmd = self.pipe.recv()
            if cmd is None:
                self.t.cancel()
                self.pipe.send(None)
                break
            try:
                result = try_(parse_(text=paste_(unicode(cmd, "UTF-8"))), silent=True)
                value, visible = try_(withVisible_(result[0]), silent=True)
                iss4 = isinstance(value, robs.methods.RS4)
                if visible[0]:
                    if iss4:
                        print value
                    elif str(value).count('NULL') < 1:
                        print value
            except Exception, value:
                print str(value)
            time.sleep(0.03)
            self.pipe.send(True)

    def update(self, interval=0.03):
        while 1:
            try:
                rint.process_revents()
            except:
                pass
            time.sleep(interval)
