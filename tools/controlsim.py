import pyqtgraph as pg
import numpy
import argparse
import pprint
import json
import os
import time

import sys
sys.path.insert(0,'.')

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
        if self.done < stop:
            self.done = stop
#        self.done    = 360 if acmode else 1820000
        print('start, stop: {:},{:}'.format(start,stop))
        
        self.app  = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()

    def reset(self):
        self.plot = []

        self.xdata = []
        self.stats = []
        for i in range(16):
            self.xdata.append( [] )
            self.stats.append( {'sum':0,'min':-1,'max':-1,'first':-1,'last':-1} )

    def color(self,idx):
        x = float(idx)/float(15)
        c = (0,0,0)
        if x < 0.5:
            c = (511*(0.5-x),511*x,0)
        else:
            c = (0,511*(1.0-x),511*(x-0.5))
        print('idx {:}  x {:}  color {:}'.format(idx,x,c))
        return c

    def execute(self, instrset):

        self.reset()

        x = 0

        engine = Engine(self.acmode)

        gframe = -1
        slast  = [0]*16
        while gframe < self.done:

            frame    = int(engine.frame)
            request  = int(engine.request)

            if self.verbose:
                print('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

            while frame == gframe:

                if self.verbose:
                    print('\t[{}] = {}'.format(engine.instr,instrset))

                request  = int(engine.request)
                instrset[engine.instr].execute(engine)

                if engine.frame != frame:
                    if self.verbose:
                        print('\tframe: {}  instr {}  request {:x}'.format
                              (frame,engine.instr,request))
                                
                    if request != 0:
                        requests = []
                        for i in range(16):
                            if request & (1<<i):
                                requests.append(i)
                                self.stats[i]['sum'] += 1
                                if self.stats[i]['last']>=0:
                                    diff = frame-slast[i]
                                    if diff < self.stats[i]['min'] or self.stats[i]['min']<0:
                                        self.stats[i]['min']=diff
                                    if diff > self.stats[i]['max']:
                                        self.stats[i]['max']=diff
                                slast[i] = frame
                                self.stats[i]['last']=frame
                                if self.stats[i]['first']<0:
                                    self.stats[i]['first']=frame
                                    
                        if frame >= self.start and frame < self.stop:
                            self.xdata[i].append(frame)

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

    def show_plots(self,title):
        q = self.win.addPlot(title=title)
        for i in range(16):
            q.plot(self.xdata[i],i,pen=None,symbolPen=None,
               symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)
               #symbol='s', pxMode=True, size=2)

        self.app.processEvents()

        input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)

def controlsim(args):

    seq = SeqUser(acmode=(args.mode=='AC'),start=args.start,stop=args.stop)

    pp = pprint.PrettyPrinter(indent=3)

    stats   = {}
    request = {}
    seqdict = {}
    seqdict['control'  ] = []

    for i in range(18):
        fname = args.pattern+'/c{}.py'.format(i)
        if os.path.exists(fname):
            config = {'title':'TITLE', 'descset':None, 'instrset':None}
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)

            t0 = time.clock()
            seq.execute(config['instrset'])
            t1 = time.clock()
            print('-- execute {} seconds'.format(t1-t0))
            #  json requires names are quoted strings
            control = (seq.xdata,seq.ydata)
            stats   = seq.stats

            fname = args.pattern+'/c{}_seqsim.json'.format(i)
            open(fname,mode='w').write(json.dumps(control))
            fname = args.pattern+'/c{j}_stats.json'.format(i)
            open(fname,mode='w').write(json.dumps(stats))

            if args.plot:
                seq.show_plots(config[title])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--pattern", required=True, help="pattern to plot")
    parser.add_argument("--start", default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop" , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode" , default='CW', help="timeslot mode [CW,AC]")
    parser.add_argument("--plot" , default=False, action=store_true, help="show plot")
    args = parser.parse_args()
    
    controlsim(args)
