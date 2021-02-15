from epics import caget, caput, camonitor

class Pv:
    def __init__(self, pvname, callback=None):
        self.pvname = pvname
        self.__value__ = None
        if callback:
            def monitor_cb(newval):
                self.__value__ = float(newval.split()[3])
                callback(err=None)
            camonitor(self.pvname, monitor_cb)

    def get(self):
        self.__value__ = caget(self.pvname)
        return self.__value__

    def put(self, newval):
        ret =  caput(self.pvname,newval)
        self.__value__ = newval
        return ret

    def monitor(self, callback):
        if callback:
            def monitor_cb(newval):
                self.__value__ = float(newval.split()[3])
                callback(err=None)
            camonitor(self.pvname, monitor_cb)

