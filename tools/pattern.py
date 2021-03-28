import json
import os
import logging

class Pattern(object):

    def __init__(self,path):
        self.base       = path
        self.path       = None
        self.dest       = {}
        self.dest_stats = {}
        self.ctrl       = {}
        self.ctrl_stats = {}
        self.charge     = None
        self.allow_seq  = None
        self.destn       = json.load(open(path+'/destn.json','r'))
        self.pcdef       = json.load(open(path+'/pcdef.json','r'))

    def _update(self):
        #  Update beam class calculations
        #  Since only a subset of allow sequences are simulated,
        #    determine the range of beam classes which they match
        #  Indices are relative: i within 'allows', c within 'beamclass' (full set)
        self.allow_seq = {}
        for d in self.dest_stats['allows']:
            beamclass = {}
            for s in range(14):  # Loop over allow sequences
                fname = self.path+'/allow_d{}_{}.json'.format(d,s)
                if os.path.exists(fname):
                    maxQ = json.load(open(fname,'r'))['maxQ']
                    for c in range(len(maxQ)-1,-1,-1):
                        if self.charge > maxQ[c]:
                            break
                        beamclass[c] = s
                else:
                    break;
            self.allow_seq[d] = beamclass

    def update(self, pattern):
        self.path = self.base+'/'+pattern 
        logging.debug('Pattern path {}'.format(self.path))
        def load_json(name,path=self.path):
            return json.loads(open(path+'/'+name+'.json','r').read())
        self.dest_stats = load_json('dest_stats')
        self.dest       = load_json('dest')
        self.ctrl_stats = load_json('ctrl_stats')
        self.ctrl       = load_json('ctrl')
        if self.charge:
            self._update()

    def chargeUpdate(self, charge):
        self.charge = charge
        if self.path:
            self._update()
        

