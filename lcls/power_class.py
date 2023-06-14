import argparse
import logging
import json
import os

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

def main(args):
    fname = args.file
    charge = args.charge
    if os.path.exists(fname):
        logging.debug(f'Loading [{fname}]')
        config = json.load(open(fname,mode='r'))
        logging.debug(config)
        print(f'power class {power_class(config,charge)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--file", required=True, help="allow file")
    parser.add_argument("--charge" , required=True, help="bunch charge, pC", type=int)
    args = parser.parse_args()

    main(args)
