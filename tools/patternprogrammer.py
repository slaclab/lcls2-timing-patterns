from tools.seqprogram import *
from threading import Lock
import json
import os
import argparse
import time
import cProfile

#  Find the lowest power class this sequence satisfies
def power_class(fname, charge):
    config = json.load(open(fname,mode='r'))
    for i,q in enumerate(config['maxQ']):
        if q is not None and charge < q:
            return i
    raise RuntimeError('power_class {} {} does not obey any'.format(fname,charge))

def patternprogrammer(pattern, charge, pv):
    profile = []
    profile.append(('init',time.time()))

    #  Setup access to all sequence engines
    #    allow seq[14]=bcs jump,  allow seq[15]=manual jump
    allowSeq   = [{'eng':SeqUser(pv+':ALW{:02d}'.format(i))} for i in range(14)]
    beamSeq    = [{'eng':SeqUser(pv+':DST{:02d}'.format(i))} for i in range(16)]
    controlSeq = [{'eng':SeqUser(pv+':EXP{:02d}'.format(i))} for i in range(18)]
    allowTbl   = [AlwUser(pv+':ALW{:02d}'.format(i)) for i in range(16)]

    profile.append(('seqdict_init',time.time()))

    #  Define restart trigger
    sync = FixedRateSync(6)  # 1Hz fixed rate
    #sync = ACRateSync(4)  # 1Hz AC rate
    restartPv = Pv(pv+':GBLSEQRESET')
    #chargePv  = Pv(pv+':GBLSEQRESET')

    # 1)  Program sequences

    #
    #  Reprogram the allow sequences found in pattern
    #    The entire allow engine/table is reloaded on the sync marker
    #
    for i,seq in enumerate(allowSeq):
        print('allowSeq {}'.format(i))
        seq['remove'] = seq['eng'].idx_list()

        newseq = {}
        pc     = {}
        #  Loop over all allow sequences
        for j in range(14):
            #  Load the sequence from the pattern directory, if it exists
            fname = pattern+'/allow_d{:}_{:}.json'.format(i,j)
            if os.path.exists(fname):
                newseq[j] = seq['eng'].loadfile(fname)[0]
                pc    [j] = power_class(fname,charge)
            else:
                pc    [j] = -1
                break

        #  Fill allow table
        lseq = 0
        lpc  = 0
        iseq = 0
        for j in range(14):
            if pc[iseq]==j:
                lseq = newseq[iseq]
                lpc  = pc    [iseq]
                iseq += 1
            #  Assign the subsequence number and power class
            allowTbl[i].seq(j,lpc,lseq)
        seq['eng'].schedule(0,sync)

    profile.append(('allowseq_prog',time.time()))
            
    #
    #  Reprogram the control sequences found in pattern
    #    Reloaded entirely on sync marker
    #
    for i,seq in enumerate(controlSeq):
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
    for i,seq in enumerate(beamSeq):
        if i==0:
            seq['remove'] = []
            continue
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
        
    # 2)  Restart
    restartPv.put(1)
    restartPv.put(0)

    profile.append(('restart',time.time()))

    #  Need to be sure the new sequences are running before removing the old
    #  Otherwise, we overwrite the running instructions
    time.sleep(1.05)

    # 3)  Clean up
    for seq in allowSeq:
        seq['eng'].remove(seq['remove'])
        
    for seq in controlSeq:
        if 'remove' in seq:
            seq['eng'].remove(seq['remove'])

    for seq in beamSeq:
        seq['eng'].remove(seq['remove'])

    profile.append(('cleanup',time.time()))

    t0 = profile[0][1]
    for p in profile:
        print(' {:20s} : {} sec'.format(p[0],p[1]-t0))
        t0 = p[1]

    print('Total time {} sec'.format(profile[-1][1]-profile[0][1]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pattern", required=True, help="pattern subdirectory")
    parser.add_argument("--charge" , required=True, help="bunch charge, pC", type=int)
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    args = parser.parse_args()

    cProfile.run('patternprogrammer(args.pattern, args.charge, args.pv)')
#    main(args)
