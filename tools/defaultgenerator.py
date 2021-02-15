import collections
import argparse
import os
from tools.destn import *
from tools.pcdef import *

class DefaultGenerator(object):
    def __init__(self, args):
        self.args = args
        self.f=open(args.output,mode='w')
        self.f.write('from tools.seq import *\n')
        self.f.write('\n')
        self.f.write('instrset = []\n')
        self.ninstr = 0  # Track # instructions to verify it will fit in instruction cache
        self.program()
        if self.ninstr > 1024:
            raise RuntimeError('Instruction cache overflow [{}]'.format(self.ninstr))
        self.f.close()

    def program(self):
        if self.args.pc == 1:
            self.f.write('instrset.append( BeamRequest(0) )\n')
            self.f.write('instrset.append( FixedRateSync(5,1) )\n')
            self.ninstr += 2
        elif self.args.pc == 2:
            self.f.write('instrset.append( BeamRequest(0) )\n')
            self.f.write('instrset.append( FixedRateSync(0,1) )\n')
            self.ninstr += 2
        self.f.write('instrset.append( Branch.unconditional(0) )\n')
        self.ninstr += 1

        self.f.close()

def main():
    parser = argparse.ArgumentParser(description='Default sequence generator')
    parser.add_argument("-o", "--output"            , required=True , 
                        help="file output path")
    args = parser.parse_args()

    GeneratorArgs = collections.namedtuple('GeneratorArgs',['output','dest','pc'])
    genargs = {}

    for d in range(len(destn)):
        genargs['dest'  ] = d
        genargs['output'] = args.output+'/d{}.py'.format(d)
        genargs['pc'    ] = 0
        gen = DefaultGenerator(GeneratorArgs(**genargs))

        for pc in range(len(pcdef)):
            genargs['output'] = args.output+'/allow_d{}_pc{}.py'.format(d,pc)
            genargs['pc'    ] = pc
            gen = DefaultGenerator(GeneratorArgs(**genargs))

if __name__ == '__main__':
    main()
