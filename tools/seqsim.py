import pyqtgraph as pg
import numpy
import argparse
#from .seq      import *
import pprint
import json
import os

import sys
sys.path.insert(0,'.')
from destn import *
from pcdef import *

f=None

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Engine(object):

    def __init__(self, acmode=False):
        self.request = 0
        self.instr   = 0
        self.frame   = -1  # 1MHz timeslot
        self.acframe = -1  # 360Hz timeslot
        self.acmode  = acmode
        self.modes   = 0
        self.ccnt    = [0]*4
        self.done    = False

    def frame_number(self):
        return int(self.acframe) if self.acmode else int(self.frame)

class SeqUser:
    def __init__(self, start=0, stop=200, acmode=False):
        global f
        self.verbose = False
        self.start   = start
        self.stop    = stop
        self.acmode  = acmode
        self.done    = 360 if acmode else 910000
#        self.done    = 360 if acmode else 1820000
        print('start, stop: {:},{:}'.format(start,stop))
        
        self.app  = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()

    def reset(self):
        self.plot = []

        self.xdata = []
        self.ydata = []
        for i in range(len(destn)):
            self.xdata.append([])
            self.ydata.append([])

        self.stats = []
        for i in range(len(destn)):
            self.stats.append( {'sum':0,'min':910000,'max':0,'last':-1} )

    def color(self,dest):
        x = float(dest)/float(len(destn)-1)
        c = (0,0,0)
        if x < 0.5:
            c = (511*(0.5-x),511*x,0)
        else:
            c = (0,511*(1.0-x),511*(x-0.5))
        print('dest {:}  x {:}  color {:}'.format(dest,x,c))
        return c

    def execute(self, seqdict):

        self.reset()

        x = 0

        request_engines = []
        for i in range(len(seqdict['request'])):
            request_engines.append(Engine(self.acmode))

        allow_engines   = []
        for i in range(len(seqdict['allow'])):
            allow_engines  .append(Engine(self.acmode))

        gframe = -1
        while gframe < self.done:

            requests  = 0
            allow     = 0
            arequest  = -1

            #  Form allow result first
            for i,engine in enumerate(allow_engines):

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['allow'][i]

                if self.verbose:
                    print('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    if self.verbose:
                        print('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        if request != 0:
                            allow    |= (1<<i)
                        if self.verbose:
                            print('\tframe: {}  instr {}  allow {:x}'.format
                                  (frame,engine.instr,allow))

                        frame   = int(engine.frame)
                        request = int(engine.request)

                        if engine.done:
                            engine.request = 0
                            break

            #  Form request and apply allow table
            for i,engine in enumerate(request_engines):

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['request'][i]

                if self.verbose:
                    print('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    if self.verbose:
                        print('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        if self.verbose:
                            print('\tframe: {}  instr {}  request {:x}'.format
                                  (frame,engine.instr,request))
                                
                        if request != 0:
                            requests |= (1<<i)

                            if allow&seqdict['allowmask'][i]==seqdict['allowmask'][i]:
                                arequest  = i

                                self.stats[i]['sum'] += 1
                                if self.stats[i]['last']>=0:
                                    diff = frame-self.stats[i]['last']
                                    if diff < self.stats[i]['min']:
                                        self.stats[i]['min']=diff
                                    if diff > self.stats[i]['max']:
                                        self.stats[i]['max']=diff
                                self.stats[i]['last']=frame

                                if frame >= self.start and frame < self.stop:
                                    self.xdata[i].append(frame)
                                    self.ydata[i].append(i)

                        if engine.done:
                            engine.request = 0
                            break
                        frame   = int(engine.frame)
                        request = int(engine.request)

            #if arequest>=0 and gframe >= self.start and gframe < self.stop:
            #    self.xdata[arequest].append(gframe)
            #    self.ydata[arequest].append(0+arequest*0.04)

            if self.verbose:
                print('== gframe {}  requests {:x}  request {}'.format(gframe,requests,arequest))
            gframe += 1

        if engine.modes == 3:
            print(bcolors.WARNING + "Found both fixed-rate-sync and ac-rate-sync instructions." + bcolors.ENDC)


        print(self.stats)

    def show_plots(self):
        q = self.win.addPlot(title='Destn')
        for i in range(len(destn)):
            q.plot(self.xdata[i],self.ydata[i],pen=None,symbolPen=None,
                   symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)

        self.app.processEvents()

        input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)

def pcGen():
    d = {}
    for i in range(len(destn)):
        d[i] = 0
    yield(d)

    done=False
    while not done:
        n = len(pcdef)-1
        for i in reversed(range(len(destn))):
            if d[i]==n:
                d[i]=0
                if i==0:
                    done=True
                    return
            else:
                d[i]+=1
                break
        yield(d)

def main():
    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--pattern", required=True, help="pattern to plot")
    parser.add_argument("--start", default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop" , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode" , default='CW', help="timeslot mode [CW,AC]")
    args = parser.parse_args()
    
    seq = SeqUser(acmode=(args.mode=='AC'),start=args.start,stop=args.stop)

    pp = pprint.PrettyPrinter(indent=3)

    stats = []
    for pc in pcGen():
        seqdict = {}
        seqdict['request'  ] = []
        seqdict['allow'    ] = []
        seqdict['allowmask'] = []

        for i in range(len(destn)): 
            fname = args.pattern+'/d{}.py'.format(i)
            if not os.path.exists(fname):
                fname = 'defaults/d{}.py'.format(i)
            config = {'title':'TITLE', 'descset':None, 'instrset':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            seqdict['request'].append(config['instrset'])

            fname = args.pattern+'/allow_d{:}_pc{:}.py'.format(i,pc[i])
            if not os.path.exists(fname):
                fname = 'defaults/allow_d{:}_pc{:}.py'.format(i,pc[i])
            config = {'title':'TITLE', 'descset':None, 'instrset':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            seqdict['allow'].append(config['instrset'])
            seqdict['allowmask'].append(destn[i]['amask'])

        #pp.pprint('seqdict[\'request\'] {:}'.format(seqdict['request']))
        #pp.pprint('seqdict[\'allow\'] {:}'.format(seqdict['allow']))
        seq.execute(seqdict)
        stats.append({'pc':pc.copy(),'stats':seq.stats})

    fname = args.pattern+'/validation.dat'
    open(fname,mode='w').write(json.dumps(stats))

    seq.show_plots()

if __name__ == '__main__':
    main()
