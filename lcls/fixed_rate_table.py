import argparse
import sys
import itertools
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple validation printing')
    parser.add_argument("-f", "--factor", required=False , type=int, default=1, help="only show Nth sub-harmonics")
    parser.add_argument("-a", "--ac", action='store_true', help="format for AC coincidence tabl")
    args = parser.parse_args()

    factors = [2,2,2,2,5,5,5,5,7,13]  # product is 910,000
    subfactors = []
    remfactors = []
    sf = args.factor
    for f in factors:
        d = sf/f
        if int(d)==d:
            sf = d
            remfactors.append(f)
        else:
            subfactors.append(f)

    rf = tuple(remfactors)

    iters = [itertools.combinations(subfactors,i+1) for i in range(len(subfactors))]
    f = set()
    d = {}
    ac = {}
    for i in iters:
        for c in i:
            q = np.prod(np.array(c))*args.factor
            f.add(q)
            d[q] = c+rf
            ac[q] = q if 13 not in d[q] else q/13

    f.add(args.factor)
    d[args.factor] = rf
    ac[args.factor] = 1.

    base = 1300.e6/1400.
    if args.factor > 1:
        print('rate, Hz\tsubfactor\tfactor\tfactors')
        for q in sorted(f):
            print('{:6d}\t{:6d}\t{:6d}\t{}'.format(int(base/float(q)),int(q/args.factor),q,d[q]))
    elif args.ac:
        print('spacing\trate, Hz\tAC %  ')
        for q in sorted(f):
            acfrac = 100./ac[q]
            print('{:6d}\t{:6d}\t{:5.2f}'.format(q,int(base/float(q)),acfrac))
    else:
        staggers=(2,4,5,7,8,10,13)
        t = 'rate, Hz\tspacing\tfactors'
        for s in staggers:
            t += f'\tx{s}'
        print(t)
        for q in sorted(f):
            t = '{:6d}\t{:6d}\t{}'.format(int(base/float(q)),q,d[q])
            for s in staggers:
                c = 'x' if q/s==int(q/s) else ' '
                t += f'\t{c}'
            print(t)
