from tools.seqprogram import *
from destn import *
from pcdef import *
from threading import Lock
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pattern", required=True, help="pattern directory")
#    parser.add_argument("--pv"     , required=True, help="TPG base pv; e.g. ")
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    args = parser.parse_args()

    #  Setup access to all sequence engines
    allowSeq   = [{'eng':SeqUser(args.pv+':ALW{:02d}'.format(i))} for i in range(16)]
    beamSeq    = [{'eng':SeqUser(args.pv+':DST{:02d}'.format(i))} for i in range(16)]
    controlSeq = [{'eng':SeqUser(args.pv+':EXP{:02d}'.format(i))} for i in range(18)]
    allowTbl   = [AlwUser(args.pv+':ALW{:02d}'.format(i)) for i in range(16)]

    #  Define restart trigger
    sync = FixedRateSync(6)  # 1Hz fixed rate
    #sync = ACRateSync(4)  # 1Hz AC rate
    restartmask = 0
    restartPv = Pv(args.pv+':SEQRESTART')

    # 1)  Program sequences
    for i,seq in enumerate(allowSeq):
        seq['remove'] = seq['eng'].idx_list()
        #  Loop over all power classes
        for j in range(len(pcdef)):
            #  Load the sequence from the pattern directory, if it exists
            fname = args.pattern+'/allow_d{:}_pc{:}.py'.format(i,j)
            #  Load from the default directory, it it doesn't exist
            if not os.path.exists(fname):
                fname = 'defaults/allow_d{:}_pc{:}.py'.format(i,j)
            config = {'title':'TITLE', 'descset':None, 'instrset':None, 'crc':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            newseq = seq['eng'].load(config)
            #  Assign the subsequence number for this power class
            allowTbl[i].seq(j,newseq)
        #  Schedule allow table refresh
        seq['eng'].schedule_allow_reload(sync)
            
    for i,seq in enumerate(controlSeq):
        fname = args.pattern+'/c{:}.py'.format(i)
        if os.path.exists(fname):
            seq['eng']['remove'] = seq['eng'].idx_list()
            config = {'title':'TITLE', 'descset':None, 'instrset':None, 'crc':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            subseq = seq['eng'].load(config)
            seq['eng'].schedule(subseq,0,sync)

    for i,seq in enumerate(beamSeq):
        seq['eng']['remove'] = seq['eng'].idx_list()
        fname = args.pattern+'/d{:}.py'.format(i)
        if not os.path.exists(fname):
            fname = 'defaults/d{:}.py'.format(i)
        config = {'title':'TITLE', 'descset':None, 'instrset':None, 'crc':None}
        exec(compile(open(fname).read(), fname, 'exec'), {}, config)
        subseq = seq['eng'].load(config)
        seq['eng'].schedule(subseq,0,sync)
        
    # 2)  Restart
    restartPv.put(1)
    restartPv.put(0)

    # 3)  Clean up
    for i in allowSeq.keys():
        allowSeq  [i]['eng'].remove(allowSeq  [i]['remove'])
        
    for i in controlSeq.keys():
        controlSeq[i]['eng'].remove(controlSeq[i]['remove'])

    for i in beamSeq.keys():
        beamSeq   [i]['eng'].remove(beamSeq   [i]['remove'])

if __name__ == 'main':
    main()
