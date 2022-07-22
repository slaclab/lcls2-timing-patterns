import numpy as np
import argparse
import sys
import glob
import json
import os
import logging
from tools.seqprogram import *
from tools.patternprogrammer import PatternProgrammer
from tools.pattern import Pattern
from tools.mpssim import MpsSim
from tools.globals import *

def toIntList(l):
    lq = l.strip('[(,').rstrip(')],')
    return [int(i) for i in lq.split(',')]

class IndexCb(object):
    def __init__(self,index,cb):
        self._index = index
        self._cb    = cb
        
    def cb(self,err=None):
        self._cb(self._index)

class Programmer(object):

    def __init__(self,pattern,pv):
        self.pattern = pattern
        self.programmer = PatternProgrammer(pv)
                    
        self.ratepv = {}
        self.ratev  = [0.]*MAXDST
        self.sumv   = [0]*MAXDST
        self.statev = [0]*MAXDST
        self.getstatepv = {}
        self.setstatepv = {}
        #  Setup the rate monitor counters
        for i in range(MAXDST):
            Pv(pv+':RM{:02d}:CTRL'     .format(i)).put(0)  # OFF
            Pv(pv+':RM{:02d}:RATEMODE' .format(i)).put(0)  # FixedRate
            Pv(pv+':RM{:02d}:FIXEDRATE'.format(i)).put(0) # 1MHz
            Pv(pv+':RM{:02d}:DESTMODE' .format(i)).put(2)  # Inclusion
            Pv(pv+':RM{:02d}:DESTMASK' .format(i)).put(1<<i)
            Pv(pv+':RM{:02d}:CTRL'     .format(i)).put(1)  # ON
            self.ratepv    [i] = Pv(pv+':RM{:02d}:CNT'         .format(i),IndexCb(i,self._rate_update).cb)
            self.getstatepv[i] = Pv(pv+':ALW{:02d}:MPSLATCH'   .format(i),IndexCb(i,self._state_update).cb)
            self.setstatepv[i] = Pv(pv+':ALW{:02d}:MPSSETSTATE'.format(i))
            self.ratepv    [i].get()
            self.getstatepv[i].get()
            self._rate_update (i)
            self._state_update(i)

    def load(self):
        self.programmer.load(self.pattern.path,self.pattern.charge) 

    def apply(self):
        self.sumv = [0]*MAXDST
        self.programmer.apply()

    def _rate_update(self, destn):
        if destn in self.ratepv:
            self.ratev[destn]  = self.ratepv[destn].__value__
            self.sumv [destn] += self.ratepv[destn].__value__

    def _state_update(self, destn):
        if destn in self.getstatepv:
            self.statev[destn] = int(self.getstatepv[destn].__value__)

def allowSetGen(bc,k):
    # loop through all permutations
    bck0 = bc[k[0]]
    d = {}
    if len(k)==1:
        for i in bck0.keys():
            d[k[0]] = bck0[i]
            yield d
    else:
        for a in allowSetGen(bc,k[1:]):
            d = a
            for i in bck0.keys():
                d[k[0]] = bck0[i]
                yield d

class AutoTest(object):

    def __init__(self, pattern, programmer, mps):
        self.pattern = pattern
        self.programmer = programmer
        self.mps = mps

        m = {os.path.basename(f).split('.')[0] for f in glob.glob(self.pattern.base+'/*')}
        if 'destn' in m:
            m.remove('destn')
        if 'pcdef' in m:
            m.remove('pcdef')
        modes = list(m)
        modes.sort()
        self.modes = modes

    def test_mode(self,m):
        p = {os.path.basename(f).split('.',1)[1] for f in glob.glob(self.pattern.base+'/'+m+'.*')}
        patts = list(p)
        patts.sort()
        for p in patts:
            self.pattern.update(m+'.'+p)
            self.test_pattern()

    def test_pattern(self):
        # loop through all combinations of allow sequences
        al = self.pattern.dest_stats['allows']
        logging.debug('allows {}'.format(al))
        # make a dictionary of sequence to beamclass
        bc = {}
        for i in al:
            bc[i] = {}
            for bclass,seq in self.pattern.allow_seq[i].items():
                bc[i][seq] = bclass
        logging.debug('bc {}'.format(bc))

        self.programmer.load()

        first = True
        for seqset in allowSetGen(bc,al):
            logging.debug('seqset {}'.format(seqset))
            #
            #  Replace this with an mpssim_tst proxy (TCP)
            #
            for a,seq in seqset.items():
                self.mps.setstate(a,seq)
            self.programmer.apply()
            time.sleep(2)
            keyl = []
            for i in al:
                c = seqset[i]
                s = self.pattern.allow_seq[i][c]
                keyl.append(s)
            key = '{}'.format(tuple(keyl))
            result = {i:(self.pattern.dest_stats[key][str(i)]['sum'],
                         self.programmer.ratev[i],
                         self.programmer.sumv[i]) for i in self.pattern.dest_stats['beams']}
            test = []
            for i in self.pattern.dest_stats['beams']:
                if result[i][0]!=int(result[i][1]):
                    test.append('RateErr')
                    break
            for i in self.pattern.dest_stats['beams']:
                if result[i][0]!=int(result[i][2]):
                    test.append('SumErr')
                    break
            if len(test)<2:
                logging.info('AutoTest: {} aseq {} result {} -- {}'.
                             format(self.pattern.path,seqset,result,test))
            else:
                logging.error('AutoTest: {} aseq {} result {} -- {}'.
                              format(self.pattern.path,seqset,result,test))

    def run(self):
        logging.info('AutoTest.run')
        for m in self.modes:
            self.test_mode(m)

def main():
    parser = argparse.ArgumentParser(description='simple pattern browser gui')
    parser.add_argument("--path", help="path to pattern directories", required=True)
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    parser.add_argument("--charge" , default=1, help="bunch charge (pC)")
    parser.add_argument("--mps_host", default='cpu-b084-pm01', help='mpssim host')
    parser.add_argument("--mps_port", default=11000, help='mpssim port')
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO )
    pattern = Pattern(args.path)
    pattern.chargeUpdate(args.charge)
    programmer = Programmer(pattern,args.pv)
    mps = MpsSim(args.mps_host,args.mps_port)
    worker = AutoTest(pattern,programmer,mps)
    worker.run()

if __name__ == '__main__':
    main()
