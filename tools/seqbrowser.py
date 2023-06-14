from PyQt5 import QtCore, QtGui, QtWidgets
from tools.pattern import Pattern
from tools.qt import *
from tools.globals import *
from tools.seq import FixedRateSync,ACRateSync
#from tools.compress import compress, decompress
from tools.seqsim import *
import pyseqsim
import pyqtgraph as pg
import numpy as np
import argparse
import sys
import logging

class SeqPattern(object):

    def __init__(self,seq,duration):
        self.ctrl       = {}
        self.ctrl_stats = {}
        #  simulate and fill ctrl,ctrl_stats

        seqdict = {'request' :{},
                   'encoding':{}}
        for s in seq:
            sengine,fname = s.split(':',1)
            engine = int(sengine)
            print(f'** engine {engine} fname {fname} **')

            config = {'title':'TITLE', 'descset':None, 'instrset':None, 'seqcodes':None, 'repeat':False}
            seq = 'from tools.seq import *\n'
            seq += open(fname).read()
            exec(compile(seq, fname, 'exec'), {}, config)
            seqdict['request'][engine] = config['instrset']

            encoding = [len(config['instrset'])]
            for instr in config['instrset']:
                encoding = encoding + instr.encoding()
            seqdict['encoding'][engine] = encoding

        start = 0
        stop  = int(duration*TPGSEC)
        if True:
            seq = SeqUser(acmode=False,start=start,stop=stop)
            print('-- Simulating...')
            t0 = time.perf_counter()
            seq.control(seqdict)
            t1 = time.perf_counter()
            print('-- SeqUser.control {} seconds'.format(t1-t0))
            s = (seq.xdata,seq.stats)
        else:
            seq = pyseqsim.controlseq(acmode=False,start=start,stop=stop)
            s = seq.execute(seqdict)

        self.ctrl       = s[0]
        self.ctrl_stats = s[1]


class PatternWaveform(pg.GraphicsWindow):
    def __init__(self,pattern):
        super(pg.GraphicsWindow, self).__init__()
        self.pattern = pattern

    def _color(idx,nidx):
        x = float(idx)/float(nidx-1)
        c = (0,0,0)
        if x < 0.5:
            c = (511*(0.5-x),511*x,0)
        else:
            c = (0,511*(1.0-x),511*(x-0.5))
        return c

    def update(self):
        #  Plotting lots of consecutive buckets with scatter points is
        #  time consuming.  Replace consecutive points with a line.
        def plot(q, x, y):
            if len(x):
                rx = []
                ry = []
                bfirst = x[0]
                bnext  = bfirst+1
                dlast  = y[0]
                for i in range(1,len(x)):
                    b = x[i]
                    if b==bnext and y[i]==dlast:
                        bnext = b+1
                    elif bnext-bfirst > 1:
                        q.plot([bfirst,bnext-1],[dlast,dlast],pen=pg.mkPen('w',width=5))
                        dlast  = y[i]
                        bfirst = b
                        bnext  = b+1
                    else:
                        rx.append(bfirst)
                        ry.append(dlast)
                        dlast  = y[i]
                        bfirst = b
                        bnext  = b+1
                if bnext-bfirst > 1:
                    q.plot([bfirst,bnext-1],[dlast,dlast],pen=pg.mkPen('w',width=5))
                else:
                    rx.append(bfirst)
                    ry.append(dlast)
                q.plot(rx, ry, pen=None,
                       symbolBrush=(255,255,255),
                       symbol='s',pxMode=True, size=2)

        #  Control Signal Plot
        a = self.getItem(1,0)
        if a is not None:
            self.removeItem(a)
        q1 = self.addPlot(title=None,col=0,row=1)
        q1.setLabel('left'  ,'Control' )
        q1.setLabel('bottom','Bucket')
        q1.showGrid(True,True)

        x = []
        y = []
        for i,seq in self.pattern.ctrl.items():
            for bit,buckets in seq.items():
                x.extend(buckets)
                y.extend([int(i)*CTLBITS+int(bit)]*len(buckets))

        ymax = np.amax(y,initial=0)
        ymin = np.amin(y,initial=255)
        plot(q1,x,y)
        q1.setRange(yRange=[ymin-0.5,ymax+0.5])

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, seq, duration):
        MainWindow.setObjectName("SequenceBrowser")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        layout = QtWidgets.QHBoxLayout()
        
        vb = QtWidgets.QVBoxLayout()

        self.pattern = SeqPattern(seq,duration)
        self.pi = PatternWaveform(self.pattern)
        self.pi.update()

        #  Ctrl Statistics table
        self.ctrl_table = CtrlStatsTableQt(self.pattern)
        self.ctrl_table.update()
        self.ctrl_table.update() # need to call twice for the column headers to appear!
        vb.addWidget(self.ctrl_table)

        layout.addWidget(self.pi)
        layout.addLayout(vb)

        self.centralWidget.setLayout(layout)
        MainWindow.setWindowTitle('sequence browser')
        MainWindow.setCentralWidget(self.centralWidget)

def main():
#    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.INFO)
    logging.info(QtCore.PYQT_VERSION_STR)

    parser = argparse.ArgumentParser(description='simple pattern browser gui')
    parser.add_argument("--seq", required=True, nargs='+', type=str, help="sequence engine:script pairs; e.g. 0:train.py")
    parser.add_argument("--time", required=False, type=float, default=1., help="simulated time (sec)")
    args = parser.parse_args()

    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.seq,args.time)
    MainWindow.updateGeometry()

    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
