from p4p.client.thread import Context

pvactx      = Context('pva')

class Pv:
    def __init__(self, pvname, callback=None):
        self.pvname = pvname
        self.__value__ = None
        if callback:
            def monitor_cb(newval):
                self.__value__ = newval.raw.value
                callback(err=None)
            self.subscription = pvactx.monitor(self.pvname, monitor_cb)

    def get(self):
        self.__value__ = pvactx.get(self.pvname).raw.value
        return self.__value__

    def put(self, newval, wait=None):
        ret =  pvactx.put(self.pvname, newval, wait=wait)
        self.__value__ = newval
        return ret

    def monitor(self, callback):
        if callback:
            def monitor_cb(newval):
                self.__value__ = newval.raw.value
                callback(err=None)
            self.subscription = pvactx.monitor(self.pvname, monitor_cb)

