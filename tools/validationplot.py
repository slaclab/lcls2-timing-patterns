import argparse
import json
import os
import glob
from destn import *

nd = len(destn)
ndnz = None
dnz  = None

def hdr_line(stat):
    return ' |{:^{width}s}'.format(stat,width=ndnz*7)

def stat_line(s,stat):
    line = ' |'
    for i in range(len(s['stats'])):
        if dnz[i]:
            line += ' {:6d}'.format(s['stats'][i][stat])
    return line

def validate(args):

    fname = args.pattern+'/validation.dat'
    stats = json.loads(open(fname,mode='r').read())

    # parse stats and destn to determine which destinations can be sparsified from display
    # destinations with no requests
    # power class destinations with no amask in destinations with requests

    global dnz
    global ndnz
    dnz  = [False]*nd
    pcnz = [False]*nd
    for s in stats:
        for i in range(len(s['stats'])):
            if s['stats'][i]['sum']:
                dnz[i] = True
                for j in range(nd):
                    if destn[i]['amask']&(1<<j):
                        pcnz[j] = True

    ndnz = 0
    npcnz = 0
    for i in range(nd):
        if dnz[i]:
            ndnz+=1
        if pcnz[i]:
            npcnz+=1

    print('{:-^{width}s}'.format('',width=npcnz*4+7*ndnz+max(3,13-npcnz*4)))
    print('{:-^{width}s}'.format(args.pattern,width=npcnz*4+7*ndnz+max(3,13-npcnz*4)))
    print('{:-^{width}s}'.format('',width=npcnz*4+7*ndnz+max(3,13-npcnz*4)))

    hdr = '{:^{width}s}'.format('PC',width=npcnz*4)
    hdr += hdr_line('Sum')
    hdr += hdr_line('Min')
    hdr += hdr_line('Max')
    hdr += hdr_line('First')
    hdr += hdr_line('Last')
    print('{:-^{width}s}'.format('',width=len(hdr)))
    print(hdr)

    hdr = ''
    for i in range(len(stats[0]['pc'])):
        if pcnz[i]:
            hdr += ' D{:02d}'.format(i)
    for j in range(5):
        hdr += ' |'
        for i in range(len(stats[0]['pc'])):
            if dnz[i]:
                hdr += '    D{:02d}'.format(i)
    print(hdr)
    print('{:-^{width}s}'.format('',width=len(hdr)))

    for s in stats:
        line = ''
        for i in range(len(s['pc'])):
            if pcnz[i]:
                line += ' {:3d}'.format(s['pc']['{}'.format(i)])
        line += stat_line(s,'sum')
        line += stat_line(s,'min')
        line += stat_line(s,'max')
        line += stat_line(s,'first')
        line += stat_line(s,'last')
        print(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple validation printing')
    parser.add_argument("--pattern", help="pattern result to plot")
    parser.add_argument("--subdirs", help="display subdirectories", required=False, default=False, action="store_true")
    args = parser.parse_args()
    if args.subdirs:
        args.subdirs = False
        subdirs = glob.glob(args.pattern+'/*')
        for s in subdirs:
            args.pattern = s
            validate(args)
    else:
        validate(args)
