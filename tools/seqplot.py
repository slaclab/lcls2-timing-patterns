import pyqtgraph as pg
import numpy
import argparse
from tools.globals import *

f=None
verbose=False

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
        return int(self.frame)

class SeqUser:
    def __init__(self, start=0, stop=200, acmode=False):
        global f
        self.start   = start
        self.stop    = stop
        self.acmode  = acmode
        self.done    = 360 if acmode else 910000
#        self.done    = 360 if acmode else 1820000
        print('start, stop: {:},{:}'.format(start,stop))

        self.app  = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()
        self.q    = self.win.addPlot(title='Trigger Bits',data=[0],row=0, col=0)
        self.q.getAxis('left').setLabel('bits')
        self.q.getAxis('bottom').setLabel('AC timeslots' if acmode else 'MHz timeslots')
        self.q.showAxis('right')
        self.q.getAxis('top').setLabel('time','sec')
        self.q.showAxis('top')
        self.q.getAxis('top').setScale((1/360) if acmode else (1400/1300e6))
        self.plot  = self.q.plot(pen=None, symbol='s', pxMode=True, size=2)
        self.xdata = []
        self.ydata = []
        self.stats = []
        for i in range(MAXDST):
            self.stats.append( {'sum':0,'min':910000,'max':0,'last':-1} )

    def execute(self, title, instrset, descset):

        x = 0

        engine  = Engine(self.acmode)
        while engine.frame_number() < self.done and not engine.done:

            frame   = engine.frame_number()
            request = int(engine.request)

            instrset[engine.instr].execute(engine)
            if engine.frame_number() != frame:
                if verbose:
                    print('frame: {}  instr {}  request {:x}'.format
                          (frame,engine.instr,request))

                if request!=0:
                    for i in range(MAXDST):
                        if (request&(1<<i)):
                            self.stats[i]['sum'] += 1
                            if self.stats[i]['last']>=0:
                                diff = frame-self.stats[i]['last']
                                if diff < self.stats[i]['min']:
                                    self.stats[i]['min']=diff
                                if diff > self.stats[i]['max']:
                                    self.stats[i]['max']=diff
                            self.stats[i]['last']=frame

                            if frame >= self.start and frame < self.stop:
                                self.xdata.append(frame)
                                self.ydata.append(i)

                frame   = engine.frame_number()
                request = int(engine.request)

        print('{:7s} {:7s} {:7s} {:7s}'.format('Line','Sum','Min Intv','Max Intv'))
        for i in range(MAXDST):
            s = self.stats[i]
            if s['sum']>0:
                print('{:7d} {:7d} {:7d} {:7d}'.format(i,s['sum'],s['min'],s['max']))

        self.plot.setData(self.xdata,self.ydata)

        self.q.setTitle(title)
        self.q.showGrid(x=True,y=False,alpha=1.0)

        if descset is not None:
            ticks = []
            for i,label in enumerate(descset):
                ticks.append( (float(i), label) )
            ax = self.q.getAxis('right')
            ax.setTicks([ticks])

        self.app.processEvents()

        if engine.modes == 3:
            print(bcolors.WARNING + "Found both fixed-rate-sync and ac-rate-sync instructions." + bcolors.ENDC)

        try:
            input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("seq", help="sequence script to plot")
    parser.add_argument("--start", default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop" , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode" , default='CW', help="timeslot mode [CW,AC]")
    args = parser.parse_args()

    config = {'title':'TITLE', 'descset':None, 'instrset':None}

    seq = 'from tools.seq import *\n'
    seq += open(args.seq).read()
    exec(compile(seq, args.seq, 'exec'), {}, config)

    seqtest = SeqUser(start=args.start,stop=args.stop,acmode=(args.mode=='AC'))
    seqtest.execute(config['title'],config['instrset'],config['descset'])

if __name__ == '__main__':
    main()
