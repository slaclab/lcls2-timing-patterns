import argparse
import json
import os
import glob
from lcls.destn import *

destn = lcls_destn()
nd = len(destn)
ndnz = None
dnz  = None

def hdr_line(stat):
    return ' |{:^{width}s}'.format(stat,width=ndnz*7)

def stat_line(s,stat):
    line = ' |'
    for i,v in enumerate(s):
        if dnz[i]:
            line += ' {:6d}'.format(v[stat])
    return line

def validate_dest(args):

    fname = args.pattern+'/dest_stats.json'
    stats = json.loads(open(fname,mode='r').read())

    # parse stats and destn to determine which destinations can be sparsified from display
    # destinations with no requests
    # power class destinations with no amask in destinations with requests

    global dnz
    global ndnz
    dnz  = [False]*nd
    pcnz = [False]*nd
    for s in stats.values():
        for i,d in enumerate(s):
            if d['sum']:
                dnz[i] = True
                for j in range(nd):
                    if j in destn[i]['allow']:
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
    for i in range(nd):
        if pcnz[i]:
            hdr += ' D{:02d}'.format(i)
    for j in range(5):
        hdr += ' |'
        for i in range(nd):
            if dnz[i]:
                hdr += '    D{:02d}'.format(i)
    print(hdr)
    print('{:-^{width}s}'.format('',width=len(hdr)))

    for k,v in stats.items():
        key = eval(k)
        line = ''
        for i in range(nd):
            if pcnz[i]:
                line += ' {:3d}'.format(key[i])
        line += stat_line(v,'sum')
        line += stat_line(v,'min')
        line += stat_line(v,'max')
        line += stat_line(v,'first')
        line += stat_line(v,'last')
        print(line)

def validate_ctrl(args):

    fname = args.pattern+'/ctrl_stats.json'
    stats = json.loads(open(fname,mode='r').read())
    print(' SEQ/Bit |  first  |  last   |   min   |   max   |   sum   |')
    for seq,d in stats.items():
        for b,stat in d.items():
            if stat['first']>=0:
                print(' {:3s},{:2s}  |{:9d}|{:9d}|{:9d}|{:9d}|{:9d}|'.
                      format(seq,b,stat['first'],stat['last'],stat['min'],stat['max'],stat['sum']))

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
            validate_dest(args)
            validate_ctrl(args)
    else:
        validate_dest(args)
        validate_ctrl(args)
