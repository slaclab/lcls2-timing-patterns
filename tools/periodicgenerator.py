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
    #  Beam Requests
    def __init__(self, period, start, charge, marker='\"910kH\"'):
        self.charge = charge
        self.async_start       = None
        self.__init__(period, start, marker)

    #  Control Requests
    def __init__(self, period, start, marker='\"910kH\"'):
        if isinstance(period,list):
            self.period    = period
            self.start     = start
        else:
            self.period    = [period]
            self.start     = [start]
        self.marker = marker

        if not numpy.less(start,period).all():
            raise ValueError('start must be less than period')

        self.desc = 'Periodic: period[{}] start[{}]'.format(period,start)
        self.instr = ['instrset = []']
        self.ninstr = 0
        self._fill_instr()
        if self.ninstr > 1024:
            raise RuntimeError('Instruction cache overflow [{}]'.format(self.ninstr))
        
    def _wait(self, intv):
        if intv <= 0:
            raise ValueError
        if intv >= 2048:
            self.instr.append('iinstr = len(instrset)')
            #  _Wait for 2048 intervals
            self.instr.append(f'instrset.append( FixedRateSync(marker={self.marker}, occ=2048) )')
            self.ninstr += 1
            if intv >= 4096:
                #  Branch conditionally to previous instruction
                self.instr.append('instrset.append( Branch.conditional(line=iinstr, counter=3, value={}) )'.format(int(intv/2048)-1))
                self.ninstr += 1

        rint = intv%2048
        if rint:
            self.instr.append(f'instrset.append( FixedRateSync(marker={self.marker}, occ={rint} ) )' )
            self.ninstr += 1

    def _fill_instr(self):
        #  Common period (subharmonic)
        period = numpy.lcm.reduce(self.period)
        #period = reduce(lcm,self.period)
        #  Brute force it to see how far we get (when will it fail?)
        print('period {}  args.period {}'.format(period,self.period))
        reps   = [period // p for p in self.period]
        bkts   = [range(self.start[i],period,self.period[i]) 
                  for i in range(len(self.period))]
        bunion = sorted(reduce(myunion,bkts))  # set of buckets with a request
        reqs   = []  # list of request values for those buckets
        for b in bunion:
#            req = 0
            req = []
            for i,bs in enumerate(bkts):
                if b in bs:
#                    req |= (1<<i)
                    req.append(i)
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
                self.instr.append('# loop: req {} of step {} and repeat {}'.format(reqs[i],bsteps[i],n))
                self.instr.append('start = len(instrset)')
                if bsteps[i]>0:
                    self._wait(bsteps[i])
                if hasattr(self,'charge'):
                    self.instr.append('instrset.append( BeamRequest({}) )'.format(self.charge))
                else:
                    self.instr.append('instrset.append( ControlRequest({}) )'.format(reqs[i]))
                self.ninstr += 1
                self.instr.append('instrset.append( Branch.conditional(start, 0, {}) )'.format(n))
                self.ninstr += 1
            else:
                if bsteps[i]>0:
                    self._wait(bsteps[i])
                if hasattr(self,'charge'):
                    self.instr.append('instrset.append( BeamRequest({}) )'.format(self.charge))
                else:
                    self.instr.append('instrset.append( ControlRequest({}) )'.format(reqs[i]))
                self.ninstr += 1
        
        #  Step to the end of the common period and repeat
        if rem > 0:
            self._wait(rem)
        self.instr.append('instrset.append( Branch.unconditional(0) )')
        self.ninstr += 1

def main():
    parser = argparse.ArgumentParser(description='Periodic sequence generator')
    parser.add_argument("-p", "--period"            , required=True , nargs='+', type=int, 
                        help="buckets between start of each train")
    parser.add_argument("-s", "--start_bucket"      , required=True , nargs='+', type=int,
                        help="starting bucket for first train")
    args = parser.parse_args()
    print('args {}'.format(args))
    gen = PeriodicGenerator(args.period, args.start_bucket)
    print('{} instructions'.format(gen.ninstr))
    for i in gen.instr:
        print('{}\n'.format(i))

if __name__ == '__main__':
    main()
