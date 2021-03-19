from PyQt5 import QtCore, QtGui, QtWidgets
#from tools.compress import compress, decompress
import pyqtgraph as pg
import numpy as np
import argparse
import sys
import glob
import json
import os

def toIntList(l):
    lq = l.strip('[(,').rstrip(')],')
    return [int(i) for i in lq.split(',')]

class LineEditLabel(QtWidgets.QWidget):
    def __init__(self, initValue='1', headLabel='', tailLabel=''):
        super(QtWidgets.QWidget,self).__init__()
        self.edit = QtWidgets.QLineEdit(initValue)
        self.edit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.edit.setValidator(QtGui.QIntValidator(1,65535))
        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QLabel(headLabel))
        h.addWidget(self.edit)
        h.addWidget(QtWidgets.QLabel(tailLabel))
        self.setLayout(h)

class Pattern(QtCore.QObject):

    patternChanged = QtCore.pyqtSignal(str, name='patternChanged')

    def __init__(self,path):
        super(QtCore.QObject,self).__init__()
        self.base       = path
        self.path       = None
        self.dest       = {}
        self.dest_stats = {}
        self.ctrl       = {}
        self.ctrl_stats = {}
        self.charge     = None
        self.allow_seq  = None
        self.destn       = json.load(open(path+'/destn.json','r'))
        self.pcdef       = json.load(open(path+'/pcdef.json','r'))

    def _update(self):
        #  Update beam class calculations
        #  Since only a subset of allow sequences are simulated,
        #    determine the range of beam classes which they match
        #  Indices are relative: i within 'allows', c within 'beamclass' (full set)
        self.allow_seq = {}
        for d in self.dest_stats['allows']:
            beamclass = {}
            for s in range(14):  # Loop over allow sequences
                fname = self.path+'/allow_d{}_{}.json'.format(d,s)
                if os.path.exists(fname):
                    maxQ = json.load(open(fname,'r'))['maxQ']
                    for c in range(len(maxQ)-1,-1,-1):
                        if self.charge > maxQ[c]:
                            break
                        beamclass[c] = s
                else:
                    break;
            self.allow_seq[d] = beamclass

    def update(self, pattern):
        self.path = self.base+'/'+pattern 
        print('Pattern path {}'.format(self.path))
        def load_json(name,path=self.path):
            return json.loads(open(path+'/'+name+'.json','r').read())
        self.dest_stats = load_json('dest_stats')
        self.dest       = load_json('dest')
        self.ctrl_stats = load_json('ctrl_stats')
        self.ctrl       = load_json('ctrl')
        if self.charge:
            self._update()
            self.patternChanged.emit(self.path)

    def chargeUpdate(self, charge):
        self.charge = charge
        if self.path:
            self._update()
            self.patternChanged.emit(self.path)
        
class PatternSelection(QtWidgets.QGroupBox):

    patternChanged = QtCore.pyqtSignal(str, name='patternChanged')
    chargeChanged  = QtCore.pyqtSignal(int, name='chargeChanged')

    def __init__(self, path, pattern):
        super(QtWidgets.QGroupBox,self).__init__('Pattern')
        self.pattern = pattern
        self.mode_select = QtWidgets.QComboBox()
        self.patt_select = QtWidgets.QComboBox()
        m = {os.path.basename(f).split('.')[0] for f in glob.glob(path+'/*')}
        m.remove('destn')
        m.remove('pcdef')
        modes = list(m)
        modes.sort()
        self.modes = modes
        self.mode_select.addItems(modes)
        self.ch = LineEditLabel('1','bunch charge','pC')
        self.ch.edit.editingFinished.connect(self._updateCharge)
        v = QtWidgets.QVBoxLayout()
        v.addWidget(self.mode_select)
        v.addWidget(self.patt_select)
        v.addWidget(self.ch)
        self.setLayout(v)
        self.mode_select.setCurrentIndex(-1)
        self.patt_select.setCurrentIndex(-1)
        self.mode_select.currentTextChanged.connect(self._updateMode)
        self.patt_select.currentTextChanged.connect(self._updatePatt)
        self.patternChanged.connect(pattern.update)
        self.chargeChanged.connect(pattern.chargeUpdate)
        self.mode_select.setCurrentIndex(0)

    def _updateMode(self, mode):
        self.patt_select.currentTextChanged.disconnect(self._updatePatt)
        self.mode = mode
        p = {os.path.basename(f).split('.')[1] for f in glob.glob(self.pattern.base+'/'+mode+'.*')}
        patts = list(p)
        patts.sort()
        self.patt_select.clear()
        self.patt_select.addItems(patts)
        self.patt_select.setCurrentIndex(-1)
        self.patt_select.currentTextChanged.connect(self._updatePatt)
        self.patt_select.setCurrentIndex(0)

    def _updatePatt(self, patt):
        self.patt = patt
        self.patternChanged.emit(self.mode+'.'+patt)

    def _updateCharge(self):
        self.chargeChanged.emit(int(self.ch.edit.text()))
       
class AllowSetSelection(QtWidgets.QGroupBox):

    changed = QtCore.pyqtSignal(str, name='changed')

    def __init__(self,pattern):
        super(QtWidgets.QGroupBox,self).__init__('Beam Class Set')
        self.pattern  = pattern

        grid = QtWidgets.QGridLayout()
        self.labels  = {}
        self.bgroups = {}
        for ii,d in self.pattern.destn.items():
            i = int(ii)
            l = QtWidgets.QLabel('D{} [{}]'.format(i,d['name']))
            self.labels[i] = l
            grid.addWidget(l,i,0)
            b = QtWidgets.QComboBox()
            b.addItems([str(c) for c in range(10,-1,-1)])
            grid.addWidget(b,i,1)
            b.setCurrentIndex(0)
            b.currentTextChanged.connect(self._changed)
            self.bgroups[i] = b
            l.hide()
            b.hide()
        self.setLayout(grid)


    def update(self, p):
        for l in self.labels.values():
            l.hide()
        for b in self.bgroups.values():
            b.hide()

        ds = self.pattern.dest_stats
        al = ds['allows']
        for i in al:
            self.labels [i].show()
            self.bgroups[i].show()

        self._changed(0)

    def _changed(self, arg):
        #  Construct the str list of allow sequences
        seq = [d[10-self.bgroups[i].currentIndex()] for i,d in self.pattern.allow_seq.items()]
        arg = str(tuple(seq))
        self.changed.emit(arg)
        

class StatisticsTable(QtWidgets.QGroupBox):
    def __init__(self, pattern):
        super(QtWidgets.QGroupBox,self).__init__('Statistics')
        self.pattern = pattern
        v = QtWidgets.QVBoxLayout()
        self.table = QtWidgets.QTableWidget()
        v.addWidget(self.table)
        self.setLayout(v)

    def update(self, key):
        ikey = toIntList(key)
        stats = self.pattern.dest_stats[key]
        beams = ['D'+str(b) for b in self.pattern.dest_stats['beams']]

        names  = ['sum','first','last','min','max']
        self.table.setRowCount(len(names)) # sum, first, last, min, max
        self.table.setVerticalHeaderLabels(names)
        self.table.setHorizontalHeaderLabels(beams)
        self.table.setColumnCount(len(stats))

        for col,b in enumerate(self.pattern.dest_stats['beams']):
            for row,n in enumerate(names):
                self.table.setItem(row,col,QtWidgets.QTableWidgetItem(str(stats[str(b)][n])))

class PatternImage(QtWidgets.QLabel):
    def __init__(self,pattern):
        super(QtWidgets.QLabel, self).__init__()
        self.pattern = pattern

    def update(self, key):
        buckets = self.pattern.dest[key][0]
        dests   = self.pattern.dest[key][1] 

        pi = QtGui.QImage(910,1000,QtGui.QImage.Format_Indexed8)
        pi.setColorTable([0xffff0000,0xff00ff00,0xff0000ff,0,0,0,0,0,0,0,0,0,0,0,0,0xffffffff])

        pi.fill(15)  # clear to background
        for i,b in enumerate(buckets):
            pi.setPixel(b%910,b//910,dests[i])
        self.setPixmap(QtGui.QPixmap.fromImage(pi))

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
        buckets = self.pattern.dest[key][0]
        dests   = self.pattern.dest[key][1] 
        #  Destination Plot
        a = self.getItem(0,0)
        if a is not None:
            self.removeItem(a)
        q0 = self.addPlot(title='Pattern',col=0,row=0)
        q0.setLabel('left'  ,'Destn' )
#        q0.setLabel('bottom','Bucket')
        q0.showGrid(True,True)
        ymax = np.amax(dests,initial=0)
        ymin = np.amin(dests,initial=15)

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
                y.extend([int(i)*16+int(bit)]*len(buckets))

        ymax = np.amax(y,initial=0)
        ymin = np.amin(y,initial=255)
        plot(q1,x,y)
        q1.setRange(yRange=[ymin-0.5,ymax+0.5])
        q1.setXLink(q0)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, path):
        MainWindow.setObjectName("PatternBrowser")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        
        layout = QtWidgets.QHBoxLayout()
        
        vb = QtWidgets.QVBoxLayout()

        self.pattern = Pattern(path)

        #  Pattern Selection
        self.pattern_select = PatternSelection(path,self.pattern)
        vb.addWidget(self.pattern_select)
        
        #  Allow sequence combination selection
        self.allow_set_select = AllowSetSelection(self.pattern)
        vb.addWidget(self.allow_set_select)

        #  Beam class combination selections

        #  Statistics table
        self.stat_table = StatisticsTable(self.pattern)
        vb.addWidget(self.stat_table)

        #self.pi = PatternImage()
        self.pi = PatternWaveform(self.pattern)

        layout.addLayout(vb)
        layout.addWidget(self.pi)
        self.centralWidget.setLayout(layout)
        MainWindow.setWindowTitle('pattern browser')
        MainWindow.setCentralWidget(self.centralWidget)

        #  Connect signals/slots
        self.pattern.patternChanged.connect(self.allow_set_select.update)
        self.allow_set_select.changed.connect(self.stat_table.update)
        self.allow_set_select.changed.connect(self.pi.update)
        #  Initialize
        self.pattern_select.mode_select.setCurrentIndex(0)
        self.pattern_select.patt_select.setCurrentIndex(0)
        self.pattern_select._updateCharge()

def main():
    print(QtCore.PYQT_VERSION_STR)

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
