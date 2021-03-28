from PyQt5 import QtCore, QtGui, QtWidgets
#from tools.compress import compress, decompress
import pyqtgraph as pg
import numpy as np
import argparse
import sys
import glob
import json
import os
import logging
from tools.seqprogram import *
from tools.patternprogrammer import PatternProgrammer
from tools.mpssim import MpsSim

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
        super(QtWidgets.QGroupBox,self).__init__('Pattern Select')
        self.pattern = pattern

        v = QtWidgets.QVBoxLayout()

        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(QtWidgets.QLabel('Mode'))
        cb = QtWidgets.QComboBox()
        hb.addWidget(cb)
        v.addLayout(hb)
        self.mode_select = cb

        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(QtWidgets.QLabel('Pattern'))
        cb = QtWidgets.QComboBox()
        hb.addWidget(cb)
        v.addLayout(hb)
        self.patt_select = cb

        m = {os.path.basename(f).split('.')[0] for f in glob.glob(path+'/*')}
        m.remove('destn')
        m.remove('pcdef')
        modes = list(m)
        modes.sort()
        self.modes = modes
        self.mode_select.addItems(modes)
        self.ch = LineEditLabel('1','bunch charge','pC')
        self.ch.edit.editingFinished.connect(self._updateCharge)
        v.addWidget(self.ch)
        self.setLayout(v)
        self.mode_select.setCurrentIndex(-1)
        self.patt_select.setCurrentIndex(-1)
        self.mode_select.currentTextChanged.connect(self._updateMode)
        self.patt_select.currentTextChanged.connect(self._updatePatt)
        self.patternChanged.connect(pattern.update)
        self.chargeChanged.connect(pattern.chargeUpdate)
#        self.mode_select.setCurrentIndex(0)

    def setMode(self, mode):
        self.mode_select.setCurrentIndex(mode)

    def setPatt(self, patt):
        self.patt_select.setCurrentIndex(patt)

    def _updateMode(self, mode):
        self.patt_select.currentTextChanged.disconnect(self._updatePatt)
        self.mode = mode
        p = {os.path.basename(f).split('.',1)[1] for f in glob.glob(self.pattern.base+'/'+mode+'.*')}
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
        self._updateCharge()

    def _updateCharge(self):
        self.chargeChanged.emit(int(self.ch.edit.text()))
       
class AllowSetSelection(QtWidgets.QGroupBox):

    allowseq_changed = QtCore.pyqtSignal(str, name='allowseq_changed')
    class_changed    = QtCore.pyqtSignal(dict, name='class_changed')

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

    def setAllow(self, a, c):
        self.bgroups[a].setCurrentIndex(10-c)

    def _changed(self, arg):
        #  Construct the str list of allow sequences
        seq = [d[10-self.bgroups[i].currentIndex()] for i,d in self.pattern.allow_seq.items()]
        arg = str(tuple(seq))
        self.allowseq_changed.emit(arg)
        #  Construct the str list of beam classes
        seq = {i:(10-self.bgroups[i].currentIndex()) for i,d in self.pattern.allow_seq.items()}
        self.class_changed.emit(seq)


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

class IndexCb(object):
    def __init__(self,index,cb):
        self._index = index
        self._cb    = cb
        
    def cb(self,err=None):
        self._cb(self._index)

class Programmer(QtWidgets.QGroupBox):

    update_table = QtCore.pyqtSignal(int,int,str, name='update_table')

    def __init__(self,pattern,pv):
        super(QtWidgets.QGroupBox, self).__init__("Programmer")
        self.pattern = pattern
        self.programmer = PatternProgrammer(pv)

        vb = QtWidgets.QVBoxLayout()

        hb = QtWidgets.QHBoxLayout()
        b = QtWidgets.QPushButton('Load')
        b.pressed.connect(self._load)
        b.setEnabled(False)
        self._loadB = b
        hb.addWidget(b)

        b = QtWidgets.QPushButton('Apply')
        b.pressed.connect(self._apply)
        b.setEnabled(False)
        self._applyB = b
        hb.addWidget(b)
        vb.addLayout(hb)

        self.table = QtWidgets.QTableWidget()
        names = ['D'+str(b) for b in range(16)]
        self.table.setRowCount(len(names)) # sum, first, last, min, max
        self.table.setVerticalHeaderLabels(names)
        stats = ['Class','Rate','Sum']
        self.table.setColumnCount(len(stats))
        self.table.setHorizontalHeaderLabels(stats)
        for i in range(16):
            self.table.setItem(i,0,QtWidgets.QTableWidgetItem(''))
            self.table.setItem(i,1,QtWidgets.QTableWidgetItem(''))
            self.table.setItem(i,2,QtWidgets.QTableWidgetItem(''))
        vb.addWidget(self.table)

        self.setLayout(vb)

        self.update_table.connect(self._table_update)

        self.ratepv = {}
        self.sumv   = [0]*16
        self.getstatepv = {}
        self.setstatepv = {}
        #  Setup the rate monitor counters
        for i in range(16):
            Pv(pv+':RM{:02d}:CTRL'     .format(i)).put(0)  # OFF
            Pv(pv+':RM{:02d}:RATEMODE' .format(i)).put(0)  # FixedRate
            Pv(pv+':RM{:02d}:FIXEDRATE'.format(i)).put(0) # 1MHz
            Pv(pv+':RM{:02d}:DESTMODE' .format(i)).put(2)  # Inclusion
            Pv(pv+':RM{:02d}:DESTMASK' .format(i)).put(1<<i)
            Pv(pv+':RM{:02d}:CTRL'     .format(i)).put(1)  # ON
            self.ratepv    [i] = Pv(pv+':RM{:02d}:CNT'         .format(i),IndexCb(i,self._rate_update).cb)
            self.getstatepv[i] = Pv(pv+':ALW{:02d}:MPSLATCH'   .format(i),IndexCb(i,self._state_update).cb)
            self.setstatepv[i] = Pv(pv+':ALW{:02d}:MPSSETSTATE'.format(i))
            self.ratepv    [i].get()
            self.getstatepv[i].get()
            self._rate_update (i)
            self._state_update(i)

    def update_pattern(self):
        self._loadB.setEnabled(True)
        self._applyB.setEnabled(False)

    def _load(self):
        self._applyB.setEnabled(False)
        self.programmer.load(self.pattern.path,self.pattern.charge) 
        self._applyB.setEnabled(True)

    def _apply(self):
        self._applyB.setEnabled(False)
        self.sumv = [0]*16
        self.programmer.apply()
        self._applyB.setEnabled(True)
        for i in range(16):
            self.update_table.emit(i, 2, str(self.sumv[i]))

    def _table_update(self, row, col, v):
        self.table.item(row,col).setText(v)

    def _rate_update(self, destn):
        if destn in self.ratepv:
            self.update_table.emit(destn, 1, str(self.ratepv[destn].__value__))
            self.sumv[destn] += self.ratepv[destn].__value__
            self.update_table.emit(destn, 2, str(self.sumv[destn]))

    def _state_update(self, destn):
        if destn in self.getstatepv:
            self.update_table.emit(destn, 0, str(int(self.getstatepv[destn].__value__)))

    #  Reassert the MPS state
    def update(self, d):
        for key,v in d.items():
            self.setstatepv[key].put(v)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, path, pv):
        MainWindow.setObjectName("patterntester")
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
        layout.addLayout(vb)

        self.pp = Programmer(self.pattern,pv)
        layout.addWidget(self.pp)

        self.centralWidget.setLayout(layout)
        MainWindow.setWindowTitle('Pattern Tester')
        MainWindow.setCentralWidget(self.centralWidget)

        #  Connect signals/slots
        self.pattern.patternChanged.connect(self.allow_set_select.update)
        self.pattern.patternChanged.connect(self.pp.update_pattern)
        self.allow_set_select.allowseq_changed.connect(self.stat_table.update)
#        self.allow_set_select.class_changed.connect(self.pp.update)
        #  Initialize
#        self.pattern_select.mode_select.setCurrentIndex(0)
#        self.pattern_select.patt_select.setCurrentIndex(0)
#        self.pattern_select._updateCharge()


def main():
    print(QtCore.PYQT_VERSION_STR)

    parser = argparse.ArgumentParser(description='simple pattern browser gui')
    parser.add_argument("--path", help="path to pattern directories", required=True)
    parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
    parser.add_argument("--mps_host", default='cpu-b084-pm01', help='mpssim host')
    parser.add_argument("--mps_port", default=11000, help='mpssim port')
    args = parser.parse_args()

    mps = MpsSim(args.mps_host,args.mps_port)

    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.path,args.pv)
    ui.allow_set_select.class_changed.connect(mps.update)
    MainWindow.updateGeometry()
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
