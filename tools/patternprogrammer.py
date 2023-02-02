from tools.seqprogram import *
from tools.pv_ca_fast import Pv
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
        if charge >= maxQ[c]:
            break
        bc = c
    if bc >= 0:
        return bc
    raise RuntimeError('power_class {} {} does not obey any'.format(fname,charge))

class PatternProgrammer(object):
    def __init__(self, pv):
        #  Setup access to all sequence engines
        #    allow seq[14]=bcs jump,  allow seq[15]=manual jump
        pv_nalw = Pv(pv+':NALW')
        pv_ndst = Pv(pv+':NDST')
        pv_nexp = Pv(pv+':NEXP')
        time.sleep(0.1)
        nalw = pv_nalw.get()
        ndst = pv_ndst.get()
        nexp = pv_nexp.get()

        self.allowSeq   = [{'eng':SeqUser(pv+':ALW{:02d}'.format(i)),'load':[],'apply':[]} for i in range(nalw)]
        self.beamSeq    = [{'eng':SeqUser(pv+':DST{:02d}'.format(i)),'load':[],'apply':[]} for i in range(ndst)]
        self.controlSeq = [{'eng':SeqUser(pv+':EXP{:02d}'.format(i)),'load':[],'apply':[]} for i in range(nexp)]
        self.allowTbl   = [AlwUser(pv+':ALW{:02d}'.format(i)) for i in range(nalw)]
        self.restartPv  = Pv(pv+':GBLSEQRESET')
        self.chargePv   = Pv(pv+':BUNCH_CHARGE_RBV')
        self.chargeEnPv = Pv(pv+':BUNCH_CHARGE_OVRD')

    def load(self, pattern, charge):
        profile = []
        profile.append(('init',time.time()))

        #  Define restart trigger
        sync = FixedRateSync("1H")  # 1Hz fixed rate
        #sync = ACRateSync(4)  # 1Hz AC rate

        # 1)  Program sequences

        #
        #  Reprogram the allow sequences found in pattern
        #    The entire allow engine/table is reloaded on the sync marker
        #
        for i,seq in enumerate(self.allowSeq):
            logging.debug('allowSeq {}'.format(i))

            # clean up what was previously loaded but not applied
            seq['eng'].remove(seq['load'])

            newseq = {}
            start  = {}
            pc     = {}
            #  Loop over all allow sequences
            for j in range(NALWSEQ):
                #  Load the sequence from the pattern directory, if it exists
                fname = pattern+'/allow_d{:}_{:}.json'.format(i,j)
                if os.path.exists(fname):
                    logging.debug(f'Loading [{fname}]')
                    config = json.load(open(fname,mode='r'))
                    logging.debug(config)
                    newseq[j] = seq['eng'].loadfile(fname)[0]
                    start [j] = config['start']
                    pc    [j] = power_class(config,charge)
                else:
                    logging.debug(f'[{fname}] not found')
                    pc    [j] = -1
                    break

            #  Fill allow table
            lseq = 0
            lpc  = 0
            lsta = 0
            iseq = 0
            for j in range(NALWSEQ):
                while (pc[iseq]==j):
                    lseq = newseq[iseq]
                    lpc  = pc    [iseq]
                    lsta = start [iseq]
                    iseq += 1
                #  Assign the subsequence number and power class
                self.allowTbl[i].seq(j,lpc,lseq,lsta)
            seq['eng'].schedule(0,sync)
            seq['load'] = newseq.values()

        profile.append(('allowseq_prog',time.time()))
            
        #
        #  Reprogram the control sequences found in pattern
        #    Reloaded entirely on sync marker
        #
        for i,seq in enumerate(self.controlSeq):
            # clean up what was previously loaded but not applied
            seq['eng'].remove(seq['load'])

            fname = pattern+'/c{:}.json'.format(i)
            if os.path.exists(fname):
                logging.debug(f'Loading [{fname}]')
                subseq = seq['eng'].loadfile(fname)[0]
                seq['eng'].schedule(subseq,sync)
                seq['load'] = [subseq,]
            else:
                logging.debug(f'[{fname}] not found')
                seq['load'] = []

        profile.append(('ctrlseq_prog',time.time()))

        #
        #  Reprogram the beam sequences found in pattern
        #    Reloaded entirely on sync marker
        #
        for i,seq in enumerate(self.beamSeq):
            # clean up what was previously loaded but not applied
            seq['eng'].remove(seq['load'])

            fname = pattern+'/d{:}.json'.format(i)
            if os.path.exists(fname):
                logging.debug(f'Loading [{fname}]')
                (subseq,allow,destn) = seq['eng'].loadfile(fname)
                seq['eng'].require(allow) 
                seq['eng'].destn  (i if destn is None else destn)
                seq['load'] = [subseq,]
            else:
                logging.debug(f'[{fname}] not found')
                subseq = 0
                seq['load'] = []
            seq['eng'].schedule(subseq,sync)

        #self.chargePv  .put(charge)
        #self.chargeEnPv.put(1)
        #save charge value for "apply"
        self.charge = charge
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

        self.chargePv.put(self.charge)
        self.chargeEnPv.put(1)
#        self.destnPv.put(self.destn)
        
        # 2)  Restart
        self.restartPv.put(1)
        self.restartPv.put(0)

        profile.append(('restart',time.time()))

        #  Need to be sure the new sequences are running before removing the old
        #  Otherwise, we overwrite the running instructions
        time.sleep(1.05)

        # 3)  Clean up
        self.clean()

        profile.append(('cleanup',time.time()))
        logging.debug(profile)
        logging.debug('Total time {} sec'.format(profile[-1][1]-profile[0][1]))

        t0 = profile[0][1]
        for p in profile:
            logging.debug(' {:20s} : {} sec'.format(p[0],p[1]-t0))
            t0 = p[1]

    def clean(self):

        #  remove everything except what was just applied
        def _clean(seq):
            # cache loaded subseqs. load is empty if already applied
            if len(seq['load']):  
                seq['apply'] = seq['load']
                seq['load'] = []
            idx_list = seq['eng'].idx_list()
            #idx_list.remove(seq['apply']) # python doesnt have this
            rm_list = [i for i in idx_list if i not in seq['apply']]
            seq['eng'].remove(rm_list)

        for seq in self.allowSeq:
            _clean(seq)

        for seq in self.controlSeq:
            _clean(seq)

        for seq in self.beamSeq:
            _clean(seq)

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

    cProfile.run('main(args)')
    main(args)
