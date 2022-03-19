import pyqtgraph as pg
import numpy
import argparse
import pprint
import json
import os
import time
import logging
from collections import deque
from itertools import chain
#from .compress import compress

destn = {}
pcdef = {}
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
        self.frame   = 0  # 1MHz timeslot
        self.acmode  = acmode
        self.ccnt    = [0]*4
        self.done    = False

    def frame_number(self):
        return int(self.frame)

class SeqUser:
    def __init__(self, start=0, stop=200, acmode=False):
        global f
        self.verbose = False
        self.start   = start
        self.stop    = stop
        self.acmode  = acmode
        self.done    = stop
        if self.done < stop:
            self.done = stop
        
    def color(self,dest):
        x = float(dest)/float(len(destn)-1)
        c = (0,0,0)
        if x < 0.5:
            c = (511*(0.5-x),511*x,0)
        else:
            c = (0,511*(1.0-x),511*(x-0.5))
        return c

    def execute(self, seqdict):

        self.plot = []

        self.xdata = []
        self.ydata = []
        slast      = {}
        self.stats = {}  # indexed by (non-contiguous) destn
        for i in seqdict['request'].keys():
            self.stats[i] = {'sum':0,'min':-1,'max':-1,'first':-1,'last':-1}

        if len(seqdict['request'])==0:
            logging.debug('No beam requests.  Skipping simulation.')
            return

        x = 0

        request_engines = {}
        for e in seqdict['request'].keys():
            request_engines[e] = Engine(self.acmode)

        allow_engines   = {}
        for a in seqdict['allow'].keys():
            allow_engines[a] = Engine(self.acmode)

        gframe = -1
        while gframe < self.done:

            requests  = 0
            allow     = 0
            arequest  = -1

            #  Form allow result first
            for i,engine in allow_engines.items():

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['allow'][i]

                logging.debug('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    logging.debug('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        if request != 0:
                            allow    |= (1<<i)
                        logging.debug('\tframe: {}  instr {}  allow {:x}'.format
                                      (frame,engine.instr,allow))

                        frame   = int(engine.frame)
                        request = int(engine.request)

                        if engine.done:
                            engine.request = 0
                            break

            #  Form request and apply allow table
            for i,engine in request_engines.items():

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['request'][i]
                amask    = seqdict['allowmask'][i]

                logging.debug('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    logging.debug('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        logging.debug('\tframe: {}  instr {}  request {:x}'.format
                                      (frame,engine.instr,request))
                                
                        if request != 0:
                            requests |= (1<<i)

                            if allow&amask==amask:
                                if i > arequest:
                                    arequest  = i

                                #  Uncomment this to record every request that passes allow
                                #if frame >= self.start and frame < self.stop:
                                #    self.xdata.append(frame)
                                #    self.ydata.append(i)

                        if engine.done:
                            engine.request = 0
                            break
                        frame   = int(engine.frame)
                        request = int(engine.request)

            #  This is the arbitrated result
            if arequest>=0 and gframe >= self.start and gframe < self.stop:
                self.xdata.append(gframe)
                self.ydata.append(arequest)

                i=arequest
                self.stats[i]['sum'] += 1
                if self.stats[i]['last']>=0:
                    diff = gframe-slast[i]
                    if diff < self.stats[i]['min'] or self.stats[i]['min']<0:
                        self.stats[i]['min']=diff
                    if diff > self.stats[i]['max']:
                        self.stats[i]['max']=diff
                slast[i] = gframe
                self.stats[i]['last']=gframe
                if self.stats[i]['first']<0:
                    self.stats[i]['first']=gframe

            logging.debug('== gframe {}  requests {:x}  request {}'.format(gframe,requests,arequest))
            gframe += 1

        #print(self.stats)

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

                logging.debug('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    logging.debug('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        logging.debug('\tframe: {}  instr {}  request {:x}'.format
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
                                slast[i][j] = frame
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

#            logging.debug('== gframe {}  requests {:x}  request {}'.format(gframe,requests,arequest))
            gframe += 1


        #print(self.stats)

    def power(self, instrset, qwin):

        result = {'spacing':910000}
        frames = {}  # dictionary of requested buckets for each window
        for q in qwin:
            if q is not None:
                result[q] = 0
                frames[q] = deque()

        request_engine = Engine(self.acmode)

        slast = None
        gframe = -1
        while gframe < self.done:

            engine = request_engine
            frame    = int(engine.frame)
            request  = int(engine.request)

#            if self.verbose:
#                print('Engine:  frame {}  request {:x}'.format(frame,request))

            while frame == gframe:

                logging.debug('\t[{}] = {}'.format(engine.instr,instrset))

                request  = int(engine.request)
                instrset[engine.instr].execute(engine)

                if engine.frame != frame:
                    logging.debug('\tframe: {}  instr {}  request {:x}'.format
                                  (frame,engine.instr,request))

                    if request:
                        if slast is not None:
                            spacing = frame - slast
                            if spacing < result['spacing']:
                                result['spacing'] = spacing
                        slast = frame

                        for q in qwin:
                            if q is not None:
                                cut = frame - q
                                frames[q].appendleft(frame)
                                while True:
                                    v=frames[q].pop()
                                    if v>cut:
                                        frames[q].append(v)
                                        break
                                if len(frames[q]) > result[q]:
                                    result[q] = len(frames[q])

#                        logging.debug('frames {}'.format(frames))
#                        logging.debug('result {}'.format(result))

                    if engine.done:
                        engine.request = 0
                        break
                    frame   = int(engine.frame)
                    request = int(engine.request)

            gframe += 1

        return result

    def show_plots(self):
        self.app  = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()

        q = self.win.addPlot(title='Destn')
        q.plot(self.xdata,self.ydata,pen=None,symbolPen=None,
               #symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)
               symbol='s', pxMode=True, size=2)

        self.app.processEvents()

        input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)

#
#  A generator for all the power class tuple combinations
#  Note that there are modes where the number of combinations is
#  too great to simulate [HXR/SXR/DiagLine delivery depends upon 
#  6 destinations x 12 power classes = 12^6 = 3M].  We may limit the 
#  simulations to the 2 highest power classes for each destination (2^6 = 64)
#
def allowSetGen(dests,seqs):
#    print('allowSetGen {} {}'.format(dests,seqs))
    nd = len(dests)
    d = [0]*nd
    for i in range(nd):
        d[i] = 0
    yield(tuple(d))

    done=False
    while not done:
        for i in range(nd):
            if d[i]==len(seqs[dests[i]])-1:
                d[i]=0
                if i==nd-1:
                    done=True
                    return
            else:
                d[i]+=1
                break
        yield(tuple(d))

#  simulate the allow sequence for determining power class
#  the result will be the range of charges for which the sequence meets each power class limits
def allowsim(instrset, pc, start=0, stop=910000, mode='CW'):
    seq = SeqUser(acmode=(mode=='AC'),start=start,stop=stop)

    #  Find all the integration windows
    qwin = { p.winQ for p in pc }

    #  Count the maximum requests in each integration window and the minimum bunch spacing
#    seq.verbose = True
    qpwr = seq.power(instrset, qwin)

    #  For each power class calculate the maximum charge for which it satisfies
    result = []
    for p in pc:
        if qpwr['spacing'] < p.spacing:
            result.append(0)
        elif p.winQ is None or qpwr[p.winQ]==0:
            result.append(0x10000)
        else:
            result.append(p.sumQ / qpwr[p.winQ])

    return result

def controlsim(pattern, start=0, stop=910000, mode='CW'):
    seq = SeqUser(acmode=(mode=='AC'),start=start,stop=stop)
    ctrl    = {}
    seqdict = {}
    seqdict['request'] = {}
    for i in range(18):
        fname = pattern+'/c{}.py'.format(i)
        config = {'title':'TITLE', 'descset':None, 'instrset':None}
        if os.path.exists(fname):
            exec(compile(open(fname).read(), fname, 'exec'), {}, config)
            seqdict['request'][i] = config['instrset']

    t0 = time.perf_counter()
    seq.control(seqdict)
    t1 = time.perf_counter()

    #seq.xdata = compress(seq.xdata)
    fname = pattern+'/ctrl.json'
    open(fname,mode='w').write(json.dumps(seq.xdata))
    fname = pattern+'/ctrl_stats.json'
    open(fname,mode='w').write(json.dumps(seq.stats))

    return seq

def seqsim(pattern, start=0, stop=910000, mode='CW', destn_list=[], pc_list=[], seq_list={}):
    global destn
    global pcdef
    destn = destn_list
    pcdef = pc_list
    
    seq = SeqUser(acmode=(mode=='AC'),start=start,stop=stop)

    #  Determine which destination power classes need to be iterated over
    beams  = []
    allows = []
    for i in range(16):
        fname = pattern+'/d{}.py'.format(i)
        if os.path.exists(fname):
            beams .append(i)
            allows.extend(destn[i]['allow'])

    allows = list(set(allows))
    allows.sort()
    if len(allows)==0:
        raise RuntimeError('No allows')

    stats = {'beams':beams,'allows':allows}
    dest  = {'beams':beams,'allows':allows}
    
    #  Loop over allow sequence combinations (across relevant destinations)
    for allowSet in allowSetGen(allows,seq_list):
        key = '{}'.format(allowSet)
#        print(key)
        seqdict = {}
        seqdict['request'  ] = {}
        seqdict['allow'    ] = {}
        seqdict['allowmask'] = {}
        for b in beams:
            fname = pattern+'/d{}.py'.format(b)
            if os.path.exists(fname):
                config = {'title':'TITLE', 'descset':None, 'instrset':None}
                exec(compile(open(fname).read(), fname, 'exec'), {}, config)
                seqdict['request'][b] = config['instrset']
                seqdict['allowmask'][b] = bitmask(destn[b]['allow'])
            else:
                raise RuntimeError('Pattern depends upon beam destination without sequence')

        for i,a in enumerate(allows):
            fname = pattern+'/allow_d{:}_{:}.py'.format(a,allowSet[i])
            if os.path.exists(fname):
                config = {'title':'TITLE', 'descset':None, 'instrset':None}
                exec(compile(open(fname).read(), fname, 'exec'), {}, config)
                seqdict['allow']    [a] = config['instrset']
            else:
                raise RuntimeError('Pattern depends upon allow sequence - not found {}'.format(fname))

#        key = str(pc)
        t0 = time.perf_counter()
        seq.execute(seqdict)
        t1 = time.perf_counter()
#        print('-- execute {} seconds'.format(t1-t0))
        #  Compress by identifying runs
        #dest [key] = compress(seq.xdata,seq.ydata)
        dest [key] = (seq.xdata,seq.ydata)
        stats[key] = {}
        for b in beams:
            stats[key][b] = seq.stats[b]

    fname = pattern+'/dest.json'
    open(fname,mode='w').write(json.dumps(dest))
    fname = pattern+'/dest_stats.json'
    open(fname,mode='w').write(json.dumps(stats))

    controlsim(pattern,start,stop,mode)

    return seq

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--pattern", required=True, help="pattern to plot")
    parser.add_argument("--start"  , default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop"   , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode"   , default='CW', help="timeslot mode [CW,AC]")
    args = parser.parse_args()
    
    seqsim(args.pattern, args.start, args.stop, args.mode, destn_list=tools.destn, pc_list=tools.pcdef).show_plots()
