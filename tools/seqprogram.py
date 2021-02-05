import time
#from psdaq.seq.seq import *
from seq import *
#from psdaq.cas.pvedit import *
from p4p.client.thread import Context
from threading import Lock
import argparse

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

class SeqUser:
    def __init__(self, base):
        prefix = base
        self.ninstr   = Pv(prefix+':INSTRCNT')
        self.desc     = Pv(prefix+':DESCINSTRS')
        self.instr    = Pv(prefix+':INSTRS')
        self.idxseq   = Pv(prefix+':SEQ00IDX')
        self.seqname  = Pv(prefix+':SEQ00DESC')
        self.seqbname = Pv(prefix+':SEQ00BDESC')
        self.idxseqr  = Pv(prefix+':RMVIDX')
        self.seqr     = Pv(prefix+':RMVSEQ')
        self.insert   = Pv(prefix+':INS')
        self.idxrun   = Pv(prefix+':RUNIDX')
#        self.clsrun   = Pv(prefix+':RUNCLASS')
        self.start    = Pv(prefix+':SCHEDRESETFLAG')
#        self.syncstart= Pv(prefix+':SCHEDRESETSYNC')
        self.reset    = Pv(prefix+':FORCERESET')
        self.running  = Pv(prefix+':RUNNING', self.changed)
        self._idx     = 0
        self.lock     = None

    def changed(self,err=None):
        q = self.running.__value__
        if q==0 and self.lock!=None:
            self.lock.release()
            self.lock=None

    def stop(self):
        self.idxrun.put(0)  # a do-nothing sequence
        self.reset .put(1)
        self.reset .put(0)

    def idx_list(self):
        r = []
        idx = self.idxseq.get()
        while (idx>0):
            r.append(idx)
            idx = self.idxseq.get()
        return r

    # Remove all existing subsequences
    def clean(self):
        ridx = -1
        print( 'Remove %d'%ridx)
        if ridx < 0:
            idx = self.idxseq.get()
            while (idx>0):
                print( 'Removing seq %d'%idx)
                self.idxseqr.put(idx)
                self.seqr.put(1)
                self.seqr.put(0)
                time.sleep(1.0)
                idx = self.idxseq.get()
        elif ridx > 1:
            print( 'Removing seq %d'%ridx)
            self.idxseqr.put(ridx)
            self.seqr.put(1)
            self.seqr.put(0)

    #  Load new sequence and return subsequence index
    def load(self, title, instrset, descset=None):
        self.desc.put(title)

        encoding = [len(instrset)]
        for instr in instrset:
            encoding = encoding + instr.encoding()

        print( encoding)

        self.instr.put( tuple(encoding) )

        time.sleep(1.0)

        ninstr = self.ninstr.get()
        if ninstr != len(instrset):
            print( 'Error: ninstr invalid %u (%u)' % (ninstr, len(instrset)))
            return

        print( 'Confirmed ninstr %d'%ninstr)

        self.insert.put(1)
        self.insert.put(0)

        #  How to handshake the insert.put -> idxseq.get (RPC?)
        time.sleep(1.0)

        #  Get the assigned sequence num
        idx = self.idxseq.get()
        if idx < 2:
            print( 'Error: subsequence index  invalid (%u)' % idx)
            raise RuntimeError("Sequence failed")

        print( 'Sequence '+self.seqname.get()+' found at index %d'%idx)

        #  (Optional for XPM) Write descriptions for each bit in the sequence
        if descset!=None:
            self.seqbname.put(descset)

        self._idx = idx
        return idx

    #  Start sequence immediately
    def begin(self, wait=False):
        self.idxrun.put(self._idx)
        self.start .put(0)
        self.reset .put(1)
        self.reset .put(0)
        if wait:
            self.lock= Lock()
            self.lock.acquire()

    #  Schedule sequence to be started on a trigger (defaults to 1Hz fixed rate)
    def schedule(self, subseq=-1, subseqclass=0, sync=FixedRateSync(6)):
        idx = subseq if subseq > 1 else self._idx
        self.idxrun.put(idx)
        self.clsrun.put(subseqclass)
        self.syncstart(sync._schedule())
        self.start.put(1)

    def schedule_allow_reload(self, sync=FixedRateSync(6)):
        self.idxrun.put(0)
        self.clsrun.put(15)  # Forces reload of subseq for current MPS state
        self.syncstart(sync._schedule())
        self.start.put(1)

    #  Stop sequence, clean out all subsequences, load new sequence, and start
    def execute(self, title, instrset, descset=None):
        self.insert.put(0)
        self.stop ()
        self.clean()
        self.load (title,instrset,descset)
        self.begin()

class AlwUser:
    def __init__(self, base):
        prefix = base
        self.tbl = {}
        for i in range(16):
            self.tbl[i] = {'idx'   :Pv(prefix+':MPS{:02d}IDX'%i),
                           'start' :Pv(prefix+':MPS{:02d}START'%i),
                           'pclass':Pv(prefix+':MPS{:02d}PCLASS'%i)}
        self.latch    = Pv(prefix+':MPSLATCH')
        self.state    = Pv(prefix+':MPSSTATE')
        self.setstate = Pv(prefix+':MPSSETSTATE')
        self.lock     = None

    def safe(self):
        state = self.state.get()
        for i in range(14):
            self.idx   .set(0)
            self.start .set(0)
            self.pclass.set(0)
        self.setstate.set(0)
        return state

def main():
    parser = argparse.ArgumentParser(description='sequence pva programming')
    parser.add_argument("seq", help="sequence script")
    parser.add_argument("pv" , help="sequence engine pv; e.g. XPM:0:SEQENG:0")
    args = parser.parse_args()
    
    config = {'title':'TITLE', 'descset':None, 'instrset':None}

    exec(compile(open(args.seq).read(), args.seq, 'exec'), {}, config)

    seq = SeqUser(args.pv)
    seq.execute(config['title'],config['instrset'],config['descset'])

if __name__ == 'main':
    main()
