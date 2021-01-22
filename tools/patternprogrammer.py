from tools.seqprogram import *
from destn import *
from pcdef import *
from threading import Lock
import time
import argparse

    def execute(self, title, instrset, descset=None):
        self.insert.put(0)
        self.stop ()
        self.clean()
        self.load (title,instrset,descset)
        self.begin()

def main():
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pattern", required=True, help="pattern directory")
    parser.add_argument("--pv"     , required=True, help="TPG base pv; e.g. ")
    args = parser.parse_args()

    # 1) Validate new pattern choice


    # 1)  Stop all sequences
    ##  Don't have PV exposed for stopping multiple sequences simultaneously
    ##  So, stop allow sequences first.  This should be clean.

    allowSeq = []
    for i in range(16):
        seq=SeqUser(args.pv+':ALW{:02d}')
        seq.stop()
        allowSeq.append( seq )

    beamSeq  = []
    for i in range(16);
        seq=SeqUser(args.pv+':DST{:02d}')
        seq.stop()
        beamSeq.append( seq )

    controlSeq = []
    for i in range(17):
        seq=SeqUser(args.pv+':EXP{:02d}')
        seq.stop()
        controlSeq.append( seq )

    # 2)  Program all allow sequences
    for i in range(len(destn)): 
        seq = allowSeq[i]
        seq.clean()

        for j in range(len(pcdef)):
            fname = args.pattern+'/allow_d{:}_pc{:}.py'.format(i,j)
            if not os.path.exists(fname):
                fname = 'defaults/allow_d{:}_pc{:}.py'.format(i,j)
            config = {'title':'TITLE', 'descset':None, 'instrset':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            seq.load(config['title'],config['instrset'])
            seq.begin()

    # 3)  Program allow table (register array)


    # 4)  Program beam generating sequences
    # 5)  Program control sequences
    # 6)  Start them all

    for i in range(16):
        
    config = {'title':'TITLE', 'descset':None, 'instrset':None}

    exec(compile(open(args.seq).read(), args.seq, 'exec'), {}, config)

    seq = SeqUser(args.pv)
    seq.execute(config['title'],config['instrset'],config['descset'])

if __name__ == 'main':
    main()
