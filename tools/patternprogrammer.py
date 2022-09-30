from tools.seqprogram import *
from threading import Lock
import json
import os
import argparse
import time
import cProfile
import logging

#  Find the lowest power class this sequence satisfies
#  It must satisfy all higher power classes
def power_class(config, charge):
    maxQ = config['maxQ']
    bc = -1
    for c in range(len(maxQ)-1,-1,-1):
        if charge > maxQ[c]:
            break
        bc = c
    if bc >= 0:
        return bc
    raise RuntimeError('power_class {} {} does not obey any'.format(fname,charge))

class PatternProgrammer(object):
    def __init__(self, pv):
        #  Setup access to all sequence engines
        #    allow seq[14]=bcs jump,  allow seq[15]=manual jump
        self.allowSeq   = []
        self.beamSeq    = []
        self.controlSeq = [{'eng':SeqUser(pv+':EXP{:02d}'.format(i))} for i in range(18)]
        self.allowTbl   = []
        self.restartPv  = [Pv(pv+':EXP{:02d}:FORCERESET'.format(i)) for i in range(17)]
        self.chargePv   = Pv(pv+':BEAMCHRG')
        self.chargeEnPv = Pv(pv+':BEAMCHRGOVRD')

    def load(self, pattern, charge):
        profile = []
        profile.append(('init',time.time()))

        #  Define restart trigger
        sync = FixedRateSync(6)  # 1Hz fixed rate
        #sync = ACRateSync(4)  # 1Hz AC rate

        # 1)  Program sequences

        #
        #  Reprogram the allow sequences found in pattern
        #    The entire allow engine/table is reloaded on the sync marker
        #
        for i,seq in enumerate(self.allowSeq):
            logging.debug('allowSeq {}'.format(i))
            seq['remove'] = seq['eng'].idx_list()
            
            newseq = {}
            start  = {}
            pc     = {}
            #  Loop over all allow sequences
            for j in range(14):
                #  Load the sequence from the pattern directory, if it exists
                fname = pattern+'/allow_d{:}_{:}.json'.format(i,j)
                if os.path.exists(fname):
                    config = json.load(open(fname,mode='r'))
                    newseq[j] = seq['eng'].loadfile(fname)[0]
                    start [j] = config['start']
                    pc    [j] = power_class(config,charge)
                else:
                    pc    [j] = -1
                    break

            #  Fill allow table
            lseq = 0
            lpc  = 0
            lsta = 0
            iseq = 0
            for j in range(14):
                if pc[iseq]==j:
                    lseq = newseq[iseq]
                    lpc  = pc    [iseq]
                    lsta = start [iseq]
                    iseq += 1
                #  Assign the subsequence number and power class
                self.allowTbl[i].seq(j,lpc,lseq,lsta)
            seq['eng'].schedule(0,sync)

        profile.append(('allowseq_prog',time.time()))
            
        #
        #  Reprogram the control sequences found in pattern
        #    Reloaded entirely on sync marker
        #
        for i,seq in enumerate(self.controlSeq):
            fname = pattern+'/c{:}.json'.format(i)
            if os.path.exists(fname):
                seq['remove'] = seq['eng'].idx_list()
                subseq = seq['eng'].loadfile(fname)[0]
                seq['eng'].schedule(subseq,sync)

        profile.append(('ctrlseq_prog',time.time()))

        #
        #  Reprogram the beam sequences found in pattern
        #    Reloaded entirely on sync marker
        #
        for i,seq in enumerate(self.beamSeq):
            seq['remove'] = seq['eng'].idx_list()
            fname = pattern+'/d{:}.json'.format(i)
            if os.path.exists(fname):
                (subseq,allow) = seq['eng'].loadfile(fname)
                seq['eng'].require(allow) 
                seq['eng'].destn  (i)
            else:
                subseq = 0
            seq['eng'].schedule(subseq,sync)


        profile.append(('beamseq_prog',time.time()))

        #  Need to program the new charge value before restart

        logging.debug('Total time {} sec'.format(profile[-1][1]-profile[0][1]))

        t0 = profile[0][1]
        for p in profile:
            logging.debug(' {:20s} : {} sec'.format(p[0],p[1]-t0))
            t0 = p[1]

    def apply(self):
        profile = []
        profile.append(('init',time.time()))

        # 2)  Restart
        for pv in self.restartPv:
            pv.put(1)
            pv.put(0)

        profile.append(('restart',time.time()))

        #  Need to be sure the new sequences are running before removing the old
        #  Otherwise, we overwrite the running instructions
        time.sleep(1.05)

        # 3)  Clean up
        #self.clean()

        profile.append(('cleanup',time.time()))

        logging.debug('Total time {} sec'.format(profile[-1][1]-profile[0][1]))

        t0 = profile[0][1]
        for p in profile:
            logging.debug(' {:20s} : {} sec'.format(p[0],p[1]-t0))
            t0 = p[1]

    def clean(self):

        for seq in self.allowSeq:
            seq['eng'].remove(seq['remove'])
            seq['remove'] = []
        
        for seq in self.controlSeq:
            if 'remove' in seq:
                seq['eng'].remove(seq['remove'])
                seq['remove'] = []

        for seq in self.beamSeq:
            seq['eng'].remove(seq['remove'])
            seq['remove'] = []

def main(args):
    p = PatternProgrammer(args.pv)
    p.load(args.pattern, args.charge)
    p.apply()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pattern", required=True, help="pattern subdirectory")
    parser.add_argument("--charge" , required=True, help="bunch charge, pC", type=int)
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    args = parser.parse_args()

    # profiler, only needed for debugging
    #cProfile.run('main(args)')
    main(args)
