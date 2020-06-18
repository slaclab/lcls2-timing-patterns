import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description='simple validation printing')
    parser.add_argument("--pattern", help="pattern result to plot")
    args = parser.parse_args()

    fname = args.pattern+'/validation.dat'
    stats = json.loads(open(fname,mode='r').read())

    nd = len(stats[0]['pc'])

    print('{:-^{width}s}'.format('',width=nd*4+7*nd+max(3,13-nd*4)))

    hdr = '{:^{width}s}'.format('PC',width=nd*4)
    hdr += ' |{:^{width}s}'.format('Sum',width=nd*7)
    hdr += ' |{:^{width}s}'.format('Min',width=nd*7)
    hdr += ' |{:^{width}s}'.format('Max',width=nd*7)
    print('{:-^{width}s}'.format('',width=len(hdr)))
    print(hdr)

    hdr = ''
    for i in range(len(stats[0]['pc'])):
        hdr += ' D{:02d}'.format(i)
    for j in range(3):
        hdr += ' |'
        for i in range(len(stats[0]['pc'])):
            hdr += '    D{:02d}'.format(i)
    print(hdr)
    print('{:-^{width}s}'.format('',width=len(hdr)))

    for s in stats:
        line = ''
        for i in range(len(s['pc'])):
            line += ' {:3d}'.format(s['pc']['{}'.format(i)])
        line += ' |'
        for i in range(len(s['stats'])):
            line += ' {:6d}'.format(s['stats'][i]['sum'])
        line += ' |'
        for i in range(len(s['stats'])):
            line += ' {:6d}'.format(s['stats'][i]['min'])
        line += ' |'
        for i in range(len(s['stats'])):
            line += ' {:6d}'.format(s['stats'][i]['max'])
        print(line)

if __name__ == '__main__':
    main()
