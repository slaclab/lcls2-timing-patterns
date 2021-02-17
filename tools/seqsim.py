import pyqtgraph as pg
import numpy
import argparse
import pprint
import json
import os
import time

#import sys
#sys.path.insert(0,'.')
from tools.destn import *
from tools.pcdef import *

f=None

def bitmask(l):
    v=0
    for i in l:
        v |= (1<<i)
    return v

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
#        self.frame   = -1  # 1MHz timeslot
#        self.acframe = -1  # 360Hz timeslot
        self.frame   = 0  # 1MHz timeslot
        self.acframe = 0  # 360Hz timeslot
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
        if self.done < stop:
            self.done = stop
#        self.done    = 360 if acmode else 1820000
        print('start, stop: {:},{:}'.format(start,stop))
        
        self.app  = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()

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

        self.plot = []

        self.xdata = []
        self.ydata = []
        self.stats = []
        for i in range(len(destn)):
            self.stats.append( {'sum':0,'min':-1,'max':-1,'first':-1,'last':-1} )

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
                amask    = seqdict['allowmask'][i]

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

                            if allow&amask==amask:
                                arequest  = i

                                self.stats[i]['sum'] += 1
                                if self.stats[i]['last']>=0:
                                    diff = frame-slast
                                    if diff < self.stats[i]['min'] or self.stats[i]['min']<0:
                                        self.stats[i]['min']=diff
                                    if diff > self.stats[i]['max']:
                                        self.stats[i]['max']=diff
                                slast = frame
                                self.stats[i]['last']=frame
                                if self.stats[i]['first']<0:
                                    self.stats[i]['first']=frame

                                if frame >= self.start and frame < self.stop:
                                    self.xdata.append(frame)
                                    self.ydata.append(i)

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

    def control(self, seqdict):

        request_engines = {}

        self.xdata = {}
        self.stats = {}
        slast = {}

        for i in seqdict['request'].keys():
            request_engines[i] = Engine(self.acmode)
            self.stats[i] = {}
            self.xdata[i] = {}
            for j in range(16):
                self.stats[i][j] = {'sum':0,'min':-1,'max':-1,'first':-1,'last':-1} 
                self.xdata[i][j] = []
            slast[i] = {}

        x = 0

        gframe = -1
        while gframe < self.done:

            #  Form request and apply allow table
            for i,engine in request_engines.items():

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
                            
                        for j in range(16):
                            if (request & (1<<j)) != 0:
                                self.stats[i][j]['sum'] += 1
                                if self.stats[i][j]['last']>=0:
                                    diff = frame-slast[i][j]
                                    if diff < self.stats[i][j]['min'] or self.stats[i][j]['min']<0:
                                        self.stats[i][j]['min']=diff
                                    if diff > self.stats[i][j]['max']:
                                        self.stats[i][j]['max']=diff
                                slast[j][j] = frame
                                self.stats[i][j]['last']=frame
                                if self.stats[i][j]['first']<0:
                                    self.stats[i][j]['first']=frame

                                if frame >= self.start and frame < self.stop:
                                    self.xdata[i][j].append(frame)

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
        q.plot(self.xdata,self.ydata,pen=None,symbolPen=None,
               #symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)
               symbol='s', pxMode=True, size=2)

        self.app.processEvents()

        input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)

#  A generator for all the power class tuple combinations
def pcGen():
    d = [0]*len(destn)
    for i in range(len(destn)):
        d[i] = 0
    yield(tuple(d))

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
        yield(tuple(d))

def seqsim(args):

    seq = SeqUser(acmode=(args.mode=='AC'),start=args.start,stop=args.stop)

    stats = {}
    dest  = {}
    for pc in pcGen():
        seqdict = {}
        seqdict['request'  ] = []
        seqdict['allow'    ] = []
        seqdict['allowmask'] = []

        for i in range(len(destn)): 
            fname = args.pattern+'/d{}.py'.format(i)
            if os.path.exists(fname):
                config = {'title':'TITLE', 'descset':None, 'instrset':None}
                exec(compile(open(fname).read(), fname, 'exec'), {}, config)
                seqdict['request'].append(config['instrset'])

                fname = args.pattern+'/allow_d{:}_pc{:}.py'.format(i,pc[i])
                if os.path.exists(fname):
                    config = {'title':'TITLE', 'descset':None, 'instrset':None}
                    exec(compile(open(fname).read(), fname, 'exec'), {}, config)
                    seqdict['allow'].append(config['instrset'])
                    seqdict['allowmask'].append(bitmask(destn[i]['allow']))

        t0 = time.clock()
        seq.execute(seqdict)
        t1 = time.clock()
        print('-- execute {} seconds'.format(t1-t0))
        #  json requires names are quoted strings
        dest ['{}'.format(pc)] = (seq.xdata,seq.ydata)
        stats['{}'.format(pc)] = seq.stats

    fname = args.pattern+'/dest.json'
    open(fname,mode='w').write(json.dumps(dest))
    fname = args.pattern+'/dest_stats.json'
    open(fname,mode='w').write(json.dumps(stats))

    ctrl  = {}
    seqdict = {}
    seqdict['request'] = {}
    for i in range(18):
        fname = args.pattern+'/c{}.py'.format(i)
        config = {'title':'TITLE', 'descset':None, 'instrset':None}
        if os.path.exists(fname):
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            seqdict['request'][i] = config['instrset']

    t0 = time.clock()
    seq.control(seqdict)
    t1 = time.clock()

    fname = args.pattern+'/ctrl.json'
    open(fname,mode='w').write(json.dumps(seq.xdata))
    fname = args.pattern+'/ctrl_stats.json'
    open(fname,mode='w').write(json.dumps(seq.stats))

    return seq

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--pattern", required=True, help="pattern to plot")
    parser.add_argument("--start", default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop" , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode" , default='CW', help="timeslot mode [CW,AC]")
    args = parser.parse_args()
    
    seqsim(args).show_plots()
