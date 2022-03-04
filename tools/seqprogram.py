import time
from tools.seq import *
#from tools.pv_ca import Pv
from tools.pv_ca_fast import Pv
from threading import Lock
import argparse
import logging

class SeqUser:

    def __init__(self, base):
        prefix = base
        self.base     = prefix
        self.ninstr   = Pv(prefix+':INSTRCNT')
        self.desc     = Pv(prefix+':DESCINSTRS')
        self.instr    = Pv(prefix+':INSTRS')
        self.idxseq   = [Pv(prefix+':SEQ{:02d}IDX'.format(i)) for i in range(64)]
        self.seqname  = Pv(prefix+':SEQ00DESC')
        self.seqbname = Pv(prefix+':SEQ00BDESC')
        self.idxseqr  = Pv(prefix+':RMVIDX')
        self.cancel   = Pv(prefix+':CNSL')
        self.idxrun   = Pv(prefix+':RUNIDX')
        self.idxaddr  = Pv(prefix+':JUMPADDR')
        self.syncstart= Pv(prefix+':SYNCSEQ')
        self.start    = Pv(prefix+':SCHEDRESETFLAG')
        self.reset    = Pv(prefix+':FORCERESET')
        self.reqmask  = Pv(prefix+':REQMASK')
        self.dest     = Pv(prefix+':DEST')

        self._newidx = False
        def idx_cb(err,self=self):
            self._newidx = True
            
        self.newidx   = Pv(prefix+':LSTIDX',callback=idx_cb)

#  Where did this come from?
#        self.running  = Pv(prefix+':RUNNING', self.changed)
        self._idx     = 0
        self.lock     = None

    def require(self, allow):
        allow_mask = 0
        for a in allow:
            allow_mask |= (1<<a)

        v = self.reqmask.get()
        if v != allow_mask:
            logging.debug('Changing allowmask {}: {} to {}'
                          .format(self.base,v,allow_mask))
            self.reqmask.put(allow_mask)

    def destn(self,d):
        v = self.dest.get()
        if v != d:
            logging.debug('Changing dest {}: {} to {}'
                          .format(self.base,v,d))
            self.dest.put(d)
            
    def stop(self):
        self.idxaddr.put(0)
        self.idxrun.put(0)  # a do-nothing sequence
        self.reset .put(1)
        self.reset .put(0)

    def idx_list(self):
        idx = []
        for pv in self.idxseq:
            i = pv.get()
            if i < 0:
                break
            idx.append(i)
        return idx

    def remove(self,idxl):
        for idx in idxl:
            logging.debug( 'Removing seq %d'%idx)
            self.idxseqr.put(idx)

    # Remove all existing subsequences
    def clean(self):
        ridx = -1
        logging.debug( 'Remove %d'%ridx)
        if ridx < 0:
            idxl = self.idx_list()
            for idx in idxl:
                logging.debug( 'Removing seq %d'%idx)
                self.idxseqr.put(idx)
        elif ridx > 1:
            logging.debug( 'Removing seq %d'%ridx)
            self.idxseqr.put(ridx)

    #  Load new sequence and return subsequence index
    def load(self, title=None, instrset=None, descset=None):
        self.cancel.put(1)
        self.cancel.put(0)

        self.desc.put(title)

        encoding = [len(instrset)]
        for instr in instrset:
            encoding = encoding + instr.encoding()

        logging.debug( encoding)

        self._newidx = False
        self.instr.put( tuple(encoding) )

        while(True):
            if self._newidx:
                break
            time.sleep(0.01)

        #  Get the assigned sequence num
        idx = self.newidx.__value__
        if idx < 2:
            err = f'Failed to load instructions for {self.base}'
            logging.error(err)
            raise RuntimeError(err)

        logging.debug( 'Sequence '+self.seqname.get()+' found at index %d'%idx)

        #  (Optional for XPM) Write descriptions for each bit in the sequence
        if descset!=None:
            self.seqbname.put(descset)

        self._idx = idx
        return idx

    #  Load new sequence and return subsequence index
    def loadfile(self, fname):
        self.cancel.put(1)
        self.cancel.put(0)

        config = json.load(open(fname,mode='r'))
        
        try:
            self.desc.put(config['title'][:35])
        except:
            raise RuntimeError('error writing {}'.format(config['title']))

        encoding = config['encoding']
        ninstw = encoding[0]

        logging.debug(encoding)

        self._newidx = False
        self.instr.put( tuple(encoding) )

        while(True):
            if self._newidx:
                break
            time.sleep(0.01)

        #  Get the assigned sequence num
        idx = self.newidx.__value__
        if idx < 2:
            logging.error( 'Error: subsequence index  invalid (%u)  fname %s' % (idx,fname))
            raise RuntimeError("Sequence failed")

        logging.debug( 'Sequence '+self.seqname.get()+' found at index %d'%idx)

        #  (Optional for XPM) Write descriptions for each bit in the sequence
        if 'descset' in config and config['descset'] is not None:
            self.seqbname.put(config['descset'])

        self._idx = idx
        
        if 'allow' in config:
            return (idx,config['allow'])

        return (idx,)

    #  Start sequence immediately
    def begin(self, wait=False):
        self.idxaddr.put(0)
        self.idxrun.put(self._idx)
        self.syncstart.put(FixedRateSync("910kH")._schedule())
        self.start .put(0)
        self.reset .put(1)
        self.reset .put(0)
        if wait:
            self.lock= Lock()
            self.lock.acquire()

    #  Schedule sequence to be started on a trigger (defaults to 1Hz fixed rate)
    #  Call with subseq=0 for allow sequence reload
    def schedule(self, subseq=-1, sync=FixedRateSync("1H")):
        idx = self._idx if subseq<0 else subseq
        self.idxaddr.put(0)
        self.idxrun.put(idx)
        self.syncstart.put(sync._schedule())
        self.start.put(1)

    #  Stop sequence, clean out all subsequences, load new sequence, and start
    def execute(self, title, instrset, descset=None):
#        self.insert.put(0)
        self.stop ()
        self.clean()
        self.load (title,instrset,descset)
        self.begin()

class AlwUser:
    def __init__(self, base):
        prefix = base
        self.tbl = {}
        for i in range(16):
            self.tbl[i] = {'idx'   :Pv(prefix+':MPS{:02d}IDX'      .format(i)),
                           'start' :Pv(prefix+':MPS{:02d}STARTADDR'.format(i)),
                           'pclass':Pv(prefix+':MPS{:02d}PCLASS'   .format(i))}
        self.latch    = Pv(prefix+':MPSLATCH')
        self.state    = Pv(prefix+':MPSSTATE')
        self.setstate = Pv(prefix+':MPSSETSTATE')
        self.lock     = None

    def seq(self, i, pc, subseq, start=0):
        self.tbl[i]['idx'   ].put(subseq)
        self.tbl[i]['start' ].put(start)
        self.tbl[i]['pclass'].put(pc)

    def safe(self):
        state = self.state.get()
        for i in range(14):
            self.tbl[i]['idx'   ].put(0)
            self.tbl[i]['start' ].put(0)
            self.tbl[i]['pclass'].put(0)
        self.setstate.put(0)
        return state

def main():
    print('main')
    parser = argparse.ArgumentParser(description='sequence pva programming')
    parser.add_argument("seq", help="sequence script")
    parser.add_argument("pv" , help="sequence engine pv; e.g. XPM:0:SEQENG:0")
    args = parser.parse_args()
#
    print('args {}'.format(args))
#
    config = {'title':'TITLE', 'descset':None, 'instrset':None}
    print('config {}'.format(config))
#
    exec(compile(open(args.seq).read(), args.seq, 'exec'), {}, config)
#
    seq = SeqUser(args.pv)
    seq.execute(config['title'],config['instrset'],config['descset'])

if __name__ == '__main__':
    main()
