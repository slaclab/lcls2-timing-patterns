import json
import os
import logging
import argparse
import pprint
from tools.globals import *

class Pattern(object):

    def __init__(self,path):
        self.base       = path
        #self.cwpath     = os.path.dirname(path)+'/CWPatterns'
        self.path       = None
        self.dest       = {}
        self.dest_stats = {}
        self.ctrl       = {}
        self.ctrl_stats = {}
        self.charge     = None
        self.allow_seq  = None   # { destination : { allow_class : max power class } }
        self.destn      = json.load(open(path+'/destn.json','r'))
        self.pcdef      = json.load(open(path+'/pcdef.json','r'))
        

    def _update(self):
        print('Pattern _update')
        if self.dest_stats is None:
            return
        #  Update beam class calculations
        #  Since only a subset of allow sequences are simulated,
        #    determine the range of beam classes which they match
        #  Indices are relative: i within 'allows', c within 'beamclass' (full set)
        self.allow_seq = {}
        for d in self.dest_stats['allows']:
            beamclass = {}
            for s in range(MAXSEQ):  # Loop over allow sequences
                fname = self.path+'/allow_d{}_{}.json'.format(d,s)
                if os.path.exists(fname):
                    maxQ = json.load(open(fname,'r'))['maxQ']
                    for c in range(len(maxQ)-1,-1,-1):
                        if self.charge > maxQ[c]:
                            break
                        beamclass[c] = s
                    print(fname)
                    print(maxQ)
                    print(beamclass)
                else:
                    break
            self.allow_seq[d] = beamclass

    def update(self, pattern):
        self.path = self.base+'/'+pattern 
        logging.debug('Pattern path {}'.format(self.path))
        def load_json(name,path=self.path):
            return json.loads(open(path+'/'+name+'.json','r').read())
        try:
            self.dest_stats = load_json('dest_stats')
            self.dest       = load_json('dest')
        except:
            self.dest_stats = None
            self.dest       = None
        self.ctrl_stats = load_json('ctrl_stats')
        self.ctrl       = load_json('ctrl')
        try:
            self.trig_stats = load_json('trig_stats')
            self.trig       = load_json('trig')
        except:
            self.trig_stats = None
            self.trig       = None
        if self.charge:
            self._update()

    def chargeUpdate(self, charge):
        print('pattern chargeUpdate')
        self.charge = charge
        if self.path:
            self._update()
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-p", "--path"  , required=True , help="files input path")
    parser.add_argument("-q", "--charge", required=False, help="charge")
    args = parser.parse_args()
    
    (pathname, patternname) = args.path.rsplit('/',1)
    pp = pprint.PrettyPrinter(indent=4)

    p = Pattern(pathname)
    print('--destn--')
    pp.pprint(p.destn)
    print('--pcdef--')
    pp.pprint(p.pcdef)

    p.update(patternname)
    print('--dest stats--')
    pp.pprint(p.dest_stats)
    print('--ctrl stats--')
    pp.pprint(p.ctrl_stats)

    if args.charge:
        p.chargeUpdate(int(args.charge))
        print('--allow seq--')
        pp.pprint(p.allow_seq)


