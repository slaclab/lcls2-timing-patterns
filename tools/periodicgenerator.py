import argparse
import json
import os
import numpy
from itertools import chain
from functools import reduce
import operator

verbose = False

#
#  Need a control sequence with periodic triggers at different rates and phasing
#  The periods will be the minimum bunch spacing for SXR and HXR delivery
#  The 'args' parameter shall have .period,.start_bucket lists for each 
#  sequence bit
#
def gcd(a,b):
    d = min(a,b)
    y = max(a,b)
    while True:
        r = y%d
        if r == 0:
            return d
        d = r

def lcm(a,b):
    return a*b // gcd(a,b)

def myunion(s0,s1):
    return set(s0) | set(s1)

class PeriodicGenerator(object):
    def __init__(self, args):
        #if len(args.period) < 2:
        #    raise ValueError('StandbyGenerator only supports up to 2 periods')
        if not numpy.less(args.start_bucket,args.period).all():
            raise ValueError('start_bucket must be less than period')

        self.args = args
        self.f=open(args.output,mode='w')
        self.f.write('from seq import *\n')
        self.f.write('\n')
        self.f.write('instrset = []\n')
        self.ninstr = 0  # Track # instructions to verify it will fit in instruction cache
        self.program()
        if self.ninstr > 1024:
            raise RuntimeError('Instruction cache overflow [{}]'.format(self.ninstr))
        self.f.close()

    def wait(self, intv):
        if intv <= 0:
            raise ValueError
        if intv >= 2048:
            self.f.write('iinstr = len(instrset)\n')
            #  Wait for 2048 intervals
            self.f.write('instrset.append( FixedRateSync(marker=0, occ=2048) )\n')
            self.ninstr += 1
            if intv >= 4096:
                #  Branch conditionally to previous instruction
                self.f.write('instrset.append( Branch.conditional(line=iinstr, counter=3, value={}) )\n'.format(int(intv/2048)-1))
                self.ninstr += 1

        rint = intv%2048
        if rint:
            self.f.write('instrset.append( FixedRateSync(marker=0, occ={} ) )\n'.format(rint))
            self.ninstr += 1

    def program(self):
        #  Common period (subharmonic)
        #period = numpy.lcm.reduce(self.args.period)
        period = reduce(lcm,self.args.period)
        #  Brute force it to see how far we get (when will it fail?)
        reps   = [period // p for p in self.args.period]
        bkts   = [range(self.args.start_bucket[i],period,self.args.period[i]) 
                  for i in range(len(self.args.period))]
        bunion = sorted(reduce(myunion,bkts))  # set of buckets with a request
        reqs   = []  # list of request values for those buckets
        for b in bunion:
            req = 0
            for i,bs in enumerate(bkts):
                if b in bs:
                    req |= (1<<i)
            reqs.append(req)

        blist  = [0] + list(bunion)
        bsteps = list(map(operator.sub,blist[1:],blist[:-1]))
        rem    = period - blist[-1]  # remainder to complete common period

        if verbose:
            print('common period {}'.format(period))
            print('bkts {}'.format(bkts))
            print('bunion {}'.format(bunion))
            print('blist {}  bsteps {}  reqs {}  rem {}'.format(blist,bsteps,reqs,rem))

        #  Reduce common steps+requests into loops
        breps = []
        nreps = 0
        for i in range(1,len(bsteps)):
            if bsteps[i]==bsteps[i-1] and reqs[i]==reqs[i-1]:
                nreps += 1
            else:
                breps.append(nreps)
                nreps = 0
        breps.append(nreps)

        i = 0
        j = 0
        for r in breps:
            if r > 0:
                del bsteps[j:j+r]
                del reqs  [j:j+r]
                if verbose:
                    print('del [{}:{}]'.format(j,j+r))
                    print('bsteps {}'.format(bsteps))
                    print('reqs   {}'.format(reqs))
            j += 1

        if verbose:
            print('breps  {}'.format(breps))
            print('bsteps {}'.format(bsteps))
            print('reqs   {}'.format(reqs))

        #  Now step to each bucket, make the request, and repeat if necessary
        for i,n in enumerate(breps):
            if n > 0:
                self.f.write('# loop: req {} of step {} and repeat {}\n'.format(reqs[i],bsteps[i],n))
                self.f.write('start = len(instrset)\n')
                if bsteps[i]>0:
                    self.wait(bsteps[i])
                self.f.write('instrset.append( ControlRequest({}) )\n'.format(reqs[i]))
                self.ninstr += 1
                if n > 1:
                    self.f.write('instrset.append( Branch.conditional(start, 0, {}) )\n'.format(n))
                    self.ninstr += 1
            else:
                if bsteps[i]>0:
                    self.wait(bsteps[i])
                self.f.write('instrset.append( ControlRequest({}) )\n'.format(reqs[i]))
                self.ninstr += 1
        
        #  Step to the end of the common period and repeat
        if rem > 0:
            self.wait(rem)
        self.f.write('instrset.append( Branch.unconditional(0) )\n')
        self.ninstr += 1

        self.f.close()

def main():
    parser = argparse.ArgumentParser(description='Periodic sequence generator')
    parser.add_argument("-o", "--output"            , required=True , 
                        help="file output path")
    parser.add_argument("-p", "--period"            , required=True , nargs='+', type=int, 
                        help="buckets between start of each train")
    parser.add_argument("-s", "--start_bucket"      , required=True , nargs='+', type=int,
                        help="starting bucket for first train")
    args = parser.parse_args()
    print('args {}'.format(args))
    gen = PeriodicGenerator(args)
    print('{} instructions'.format(gen.ninstr))

if __name__ == '__main__':
    main()
