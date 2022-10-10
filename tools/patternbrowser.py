from PyQt5 import QtCore, QtGui, QtWidgets
from tools.pattern import Pattern
from tools.qt import *
from tools.globals import *
from tools.seq import FixedRateSync,ACRateSync
#from tools.compress import compress, decompress
import pyqtgraph as pg
import numpy as np
import argparse
import sys
import logging

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

    def update(self, key):
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

        q0 = None
        if self.pattern.dest is not None:
            #  Destination Plot
            a = self.getItem(0,0)
            if a is not None:
                self.removeItem(a)
                
            if key is not None:
                buckets = self.pattern.dest[key][0]
                dests   = self.pattern.dest[key][1] 

                q0 = self.addPlot(title='Pattern',col=0,row=0)
                q0.setLabel('left'  ,'Destn' )
        #        q0.setLabel('bottom','Bucket')
                q0.showGrid(True,True)
                ymax = np.amax(dests,initial=0)
                ymin = np.amin(dests,initial=15)

                plot(q0,buckets,dests)
                q0.setRange(yRange=[ymin-0.5,ymax+0.5])

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
        if q0 is not None:
            q1.setXLink(q0)

        # Trigger plot
        q2 = None
        if self.pattern.trig is not None:
            a = self.getItem(2,0)
            if a is not None:
                self.removeItem(a)

            if key is not None:
                q2 = self.addPlot(title=None,col=0,row=2)
                q2.setLabel('left'  ,'Trigger' )
                q2.setLabel('bottom','Bucket')
                q2.showGrid(True,True)
                x = []
                y = []
                trigs = self.pattern.trig[key]
                for i,buckets in trigs.items():
                    x.extend(buckets)
                    y.extend([int(i)]*len(buckets))

                ymax = np.amax(y,initial=0)
                ymin = np.amin(y,initial=255)
                plot(q2,x,y)
                q2.setRange(yRange=[ymin-0.5,ymax+0.5])
                if q0 is not None:
                    q2.setXLink(q0)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, path):
        MainWindow.setObjectName("PatternBrowser")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        layout = QtWidgets.QHBoxLayout()
        
        vb = QtWidgets.QVBoxLayout()

        self.pattern = PatternQt(path)

        #  Pattern Selection
        self.pattern_select = PatternSelectionQt(path,self.pattern)
        vb.addWidget(self.pattern_select)
        
        #  Allow sequence combination selection
        self.allow_set_select = AllowSetSelectionQt(self.pattern)
        vb.addWidget(self.allow_set_select)

        #  Beam class combination selections

        #self.pi = PatternImage()
        self.pi = PatternWaveform(self.pattern)

        vb2 = QtWidgets.QVBoxLayout()

        #  Destn Statistics table
        self.dest_table = StatisticsTableQt(self.pattern)
        vb2.addWidget(self.dest_table)

        #  Ctrl Statistics table
        self.ctrl_table = CtrlStatsTableQt(self.pattern)
        vb2.addWidget(self.ctrl_table)

        #  Trigger Statistics table
        self.trig_table = TrigStatsTableQt(self.pattern)
        vb2.addWidget(self.trig_table)

        layout.addLayout(vb)
        layout.addWidget(self.pi)
        layout.addLayout(vb2)

        self.centralWidget.setLayout(layout)
        MainWindow.setWindowTitle('pattern browser')
        MainWindow.setCentralWidget(self.centralWidget)

        #  Connect signals/slots
        self.pattern.signal.changed.connect(self.allow_set_select.update)
        self.pattern.signal.changed.connect(self.ctrl_table.update)
        self.allow_set_select.allowseq_changed.connect(self.dest_table.update)
        self.allow_set_select.allowseq_changed.connect(self.trig_table.update)
        self.allow_set_select.allowseq_changed.connect(self.pi.update)
        #  Initialize
        self.pattern_select.mode_select.setCurrentIndex(0)
        self.pattern_select.patt_select.setCurrentIndex(0)
        self.pattern_select._updateCharge()

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(QtCore.PYQT_VERSION_STR)

    parser = argparse.ArgumentParser(description='simple pattern browser gui')
    parser.add_argument("--path", help="path to pattern directories", required=True)
    args = parser.parse_args()

    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.path)
    MainWindow.updateGeometry()

    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
