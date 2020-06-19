import argparse
import json
import os

class TrainGenerator(object):
    def __init__(self, args):
        self.args = args
        self.f=open(args.output,mode='w')
        self.f.write('from seq import *\n')
        self.f.write('\n')
        self.f.write('instrset = []\n')
        self.f.write('instrset.append(FixedRateSync(marker=6,occ=1))\n')
        self.program()

    def train(self, cc):
        intb = self.args.bunch_spacing
        nb   = self.args.bunches_per_train
        w    = 0
        self.f.write('#   {} bunches / train\n'.format(nb))
        self.f.write('instrset.append(BeamRequest(0))\n')
        if nb>1:
            self.f.write('iinstr=len(instrset)\n')
            self.wait(intb)
            self.f.write('instrset.append(BeamRequest(0))\n')
            if nb>2:
                self.f.write('instrset.append(Branch.conditional(line=iinstr,counter={},value={}))\n'.format(cc,nb-2))
            w = intb*(nb-1)
        return w

    def wait(self, intv):
        if intv <= 0:
            raise ValueError
        if intv >= 2048:
            self.f.write('iinstr = len(instrset)\n')
            #  Wait for 2048 intervals
            self.f.write('instrset.append( FixedRateSync(marker=0, occ=2048) )\n')
            if intv >= 4096:
                #  Branch conditionally to previous instruction
                self.f.write('instrset.append( Branch.conditional(line=iinstr, counter=3, value={}) )\n'.format(int(intv/2048)-1))

        rint = intv%2048
        if rint:
            self.f.write('instrset.append( FixedRateSync(marker=0, occ={} ) )\n'.format(rint))

    def program(self):
        #  How many times to repeat beam requests in "1 second"
        #  nint = 910000/intv
        #  Global sync counts as 1 cycle
        nint = self.args.trains_per_second
        intv = self.args.train_spacing
        if nint==0:
            nint = 910000/intv

        if nint>1:
            print('Generating {} trains with {} train spacing'.
                  format(nint,intv))
        if self.args.bunches_per_train>1:
            print('\tcontaining {} bunches with {} spacing'.
                  format(self.args.bunches_per_train,
                         self.args.bunch_spacing))

        #  Initial validation
        if (nint-1)*intv+(self.args.bunches_per_train-1)*self.args.bunch_spacing) >= 910000:
            raise ValueError

        rint = nint % 256
        if rint:
            self.f.write('# loop A: {} trains\n'.format(rint))
            self.f.write('startreq = len(instrset)\n')
            self.wait(intv-self.train(1))
            self.f.write('instrset.append( Branch.conditional(startreq, 0, {}) )\n'.format(rint-1))
            self.f.write('# end loop A\n')
            nint = nint - rint

        rint = (nint/256) % 256
        if rint:
            self.f.write('# loop B: {} trains\n'.format(rint*256))
            self.f.write('startreq = len(instrset)\n')
            self.wait(intv-self.train(2))
            self.f.write('instrset.append( Branch.conditional(startreq, 0, 255) )\n')
            self.f.write('instrset.append( Branch.conditional(startreq, 1, {}) )\n'.format(rint-1))
            self.f.write('# end loop B\n')
            nint = nint - rint*256

        rint = (nint / (256*256)) % 256
        if rint:
            self.f.write('# loop C: {} trains\n'.format(rint*256*256))
            self.f.write('# loop (ntrains / 256)\n')
            self.f.write('startreq = len(instrset)\n')
            self.wait(intv-self.train(3))  # can use counter 3 here because no delay can be greater than 4096 (actually 3554)
            self.f.write('instrset.append( Branch.conditional(startreq, 0, 255) )\n')
            self.f.write('instrset.append( Branch.conditional(startreq, 1, 255) )\n')
            self.f.write('instrset.append( Branch.conditional(startreq, 2, {}) )\n'.format(rint-1))
            self.f.write('# end loop C\n')
            nint = nint - rint*256*256

        if self.args.repeat:
            #  Unconditional branch (opcode 2) to instruction 0 (1Hz sync)
            self.f.write('instrset.append( Branch.unconditional(0) )\n')
        else:
            #  Unconditional branch to here
            self.f.write('startreq = len(instrset)\n')
            self.f.write('instrset.append( Branch.unconditional(startreq) )\n')

        self.f.close()

def main():
    parser = argparse.ArgumentParser(description='simple validation printing')
    parser.add_argument("-o", "--output"            , required=True , help="file output path")
    parser.add_argument("-t", "--train_spacing"     , required=True , type=int, help="buckets between start of each train")
    parser.add_argument("-N", "--trains_per_second" , required=False, type=int, help="number of trains per TPG second", default=0)
    parser.add_argument("-b", "--bunch_spacing"     , required=True , type=int, help="buckets between bunches within train")
    parser.add_argument("-n", "--bunches_per_train" , required=True , type=int, help="number of bunches in each train")
    parser.add_argument("-r", "--repeat"            , required=False , help="number of bunches in each train", default=False)
    args = parser.parse_args()
    TrainGenerator(args)

if __name__ == '__main__':
    main()
