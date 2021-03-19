import collections
import argparse
import os
#import lcls
from lcls.destn import *
from lcls.pcdef import *
from tools.seqlookup import seq_lookup
from tools.seqwrite  import beam_write, allow_write


def main():
    parser = argparse.ArgumentParser(description='Default sequence generator')
    parser.add_argument("-o", "--output"            , required=True , 
                        help="file output path")
    args = parser.parse_args()

    #  Manual listing of allow sequences
    seq_list = ['0 Hz', '0 Hz', '1 Hz', '10 Hz', '50 Hz', '100 Hz', '500 Hz', '1 kHz', '5 kHz', '10 kHz', '31 kHz', '93 kHz', '186 kHz', '929 kHz']
    
    for d in lcls_destn().keys():
        # Destination beam sequence
        beam_write(name='0 Hz', instr=seq_lookup('0 Hz'), output=args.output+'/d{}'.format(d), allow=[])
        # Allow sequences
        for pc in range(14):
            allow_write(name=seq_list[pc], instr=seq_lookup(seq_list[pc]), pcdef=lcls_pcdef(), output=args.output+'/allow_d{}_{}'.format(d,pc))


if __name__ == '__main__':
    main()

