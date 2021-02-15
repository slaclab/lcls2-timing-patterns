from tools.seqprogram import *
from tools.destn import *
from tools.pcdef import *
from threading import Lock
import os
import argparse
import time
import cProfile

def main():
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pattern", required=True, help="pattern subdirectory")
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    args = parser.parse_args()

    profile = []
    profile.append(('init',time.time()))

    #  Setup access to all sequence engines
    allowSeq   = [{'eng':SeqUser(args.pv+':ALW{:02d}'.format(i))} for i in range(len(destn))]
    beamSeq    = [{'eng':SeqUser(args.pv+':DST{:02d}'.format(i))} for i in range(len(destn))]
    controlSeq = [{'eng':SeqUser(args.pv+':EXP{:02d}'.format(i))} for i in range(18)]
    allowTbl   = [AlwUser(args.pv+':ALW{:02d}'.format(i)) for i in range(16)]

    profile.append(('seqdict_init',time.time()))

    #  Define restart trigger
    sync = FixedRateSync(6)  # 1Hz fixed rate
    #sync = ACRateSync(4)  # 1Hz AC rate
    restartmask = 0
    restartPv = Pv(args.pv+':GBLSEQRESET')

    # 1)  Program sequences
    for i,seq in enumerate(allowSeq):
        seq['remove'] = seq['eng'].idx_list()
        #  Loop over all power classes
        for j in range(len(pcdef)):
            #  Load the sequence from the pattern directory, if it exists
            fname = args.pattern+'/allow_d{:}_pc{:}.json'.format(i,j)
            #  Load from the default directory, it it doesn't exist
            if not os.path.exists(fname):
                fname = 'defaults/allow_d{:}_pc{:}.json'.format(i,j)

            newseq = seq['eng'].loadfile(fname)
            #  Assign the subsequence number for this power class
            print('Assign table {} pc {} subseq {}'.format(i,j,newseq))
            allowTbl[i].seq(j,newseq)
        seq['eng'].schedule(0,sync)

    profile.append(('allowseq_prog',time.time()))
            
    for i,seq in enumerate(controlSeq):
        fname = args.pattern+'/c{:}.json'.format(i)
        if os.path.exists(fname):
            seq['remove'] = seq['eng'].idx_list()
            subseq = seq['eng'].loadfile(fname)
            seq['eng'].schedule(subseq,sync)

    profile.append(('ctrlseq_prog',time.time()))

    for i,seq in enumerate(beamSeq):
        seq['remove'] = seq['eng'].idx_list()
        fname = args.pattern+'/d{:}.json'.format(i)
        if not os.path.exists(fname):
            fname = 'defaults/d{:}.json'.format(i)
        subseq = seq['eng'].loadfile(fname)
        seq['eng'].schedule(subseq,sync)
        seq['eng'].require(destn[i]['amask'])
        seq['eng'].destn  (i)

    profile.append(('beamseq_prog',time.time()))
        
    # 2)  Restart
    restartPv.put(1)
    restartPv.put(0)

    profile.append(('restart',time.time()))

    #  Need to be sure the new sequences are running before removing the old
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
    cProfile.run('main()')
#    main()
