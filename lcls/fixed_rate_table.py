import argparse
import sys
import itertools
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple validation printing')
    parser.add_argument("-f", "--factor", required=False , type=int, default=1, help="only show Nth sub-harmonics")
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
    for i in iters:
        for c in i:
            q = np.prod(np.array(c))*args.factor
            f.add(q)
            d[q] = c+rf

    f.add(args.factor)
    d[args.factor] = rf

    base = 1300.e6/1400.
    if args.factor > 1:
        print(' rate, Hz  | subfactor | factor | factors')
        for q in sorted(f):
            print(' {:6d}        {:6d}   {:6d}   {}'.format(int(base/float(q)),int(q/args.factor),q,d[q]))
    else:
        print(' rate, Hz  | factor | factors')
        for q in sorted(f):
            print(' {:6d}     {:6d}   {}'.format(int(base/float(q)),q,d[q]))
