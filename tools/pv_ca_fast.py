import epics
import logging

#
#  Replicate caget, caput, camonitor but retain channel connections
#  
class Pv:
    def __init__(self, pvname, callback=None):
        self.pvname = pvname
        doconnect = callback is not None
        self._pv = epics.get_pv(pvname,connect=doconnect)
        self.__value__ = None
        if callback:
            def monitor_cb(**kwargs):
                if 'value' in kwargs:
                    self.__value__ = float(kwargs['value'])
                callback(err=None)
            if self._pv.connected:
                self._pv.get()
                self._pv.add_callback(monitor_cb, index=-999, with_ctrlvars=True)
            else:
                logging.error(f'monitor failed.  {self.pvname} not connected.')

    def get(self):
        if self._pv.connected:
            val = self._pv.get(count=None, timeout=5.0,
                               use_monitor=False,
                               as_string=False,
                               as_numpy=True)
            epics.poll()
            self.__value__ = val
        return self.__value__

    def put(self, newval):
        if self._pv.connected:
            ret = self._pv.put(newval, wait=False, timeout=60)
        self.__value__ = newval
        return ret

    def monitor(self, callback):
        if callback:
            def monitor_cb(newval):
                self.__value__ = float(newval.split()[3])
                callback(err=None)
            if self._pv.connected:
                self._pv.get()
                self._pv.add_callback(monitor_cb, index=-999, with_ctrlvars=True)
            else:
                logging.error(f'monitor failed.  {self.pvname} not connected.')

