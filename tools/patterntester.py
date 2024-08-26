from PyQt5 import QtCore, QtGui, QtWidgets
import argparse
import sys
import logging
from tools.seqprogram import *
from tools.patternprogrammer import PatternProgrammer
from tools.mpssim import MpsSim
from tools.pattern import Pattern
from tools.qt import *
from tools.globals import *

def toIntList(l):
    lq = l.strip('[(,').rstrip(')],')
    return [int(i) for i in lq.split(',')]

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
        names = ['D'+str(b) for b in range(MAXDST)]
        self.table.setRowCount(len(names)) # sum, first, last, min, max
        self.table.setVerticalHeaderLabels(names)
        stats = ['Class','Rate','Sum']
        self.table.setColumnCount(len(stats))
        self.table.setHorizontalHeaderLabels(stats)
        for i in range(MAXDST):
            self.table.setItem(i,0,QtWidgets.QTableWidgetItem(''))
            self.table.setItem(i,1,QtWidgets.QTableWidgetItem(''))
            self.table.setItem(i,2,QtWidgets.QTableWidgetItem(''))
        vb.addWidget(self.table)

        self.setLayout(vb)

        self.update_table.connect(self._table_update)

        self.ratepv = {}
        self.sumv   = [0]*MAXDST
        self.getstatepv = {}
        self.setstatepv = {}
        #  Setup the rate monitor counters
        for i in range(MAXDST):
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
        self.sumv = [0]*MAXDST
        self.programmer.apply()
        self._applyB.setEnabled(True)
        for i in range(MAXDST):
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

        self.pattern = PatternQt(path)

        #  Pattern Selection
        self.pattern_select = PatternSelectionQt(path,self.pattern)
        vb.addWidget(self.pattern_select)
        
        #  Allow sequence combination selection
        self.allow_set_select = AllowSetSelectionQt(self.pattern)
        vb.addWidget(self.allow_set_select)

        #  Beam class combination selections

        #  Statistics table
        self.stat_table = StatisticsTableQt(self.pattern)
        vb.addWidget(self.stat_table)
        layout.addLayout(vb)

        self.pp = Programmer(self.pattern,pv)
        layout.addWidget(self.pp)

        self.centralWidget.setLayout(layout)
        MainWindow.setWindowTitle('Pattern Tester')
        MainWindow.setCentralWidget(self.centralWidget)

        #  Connect signals/slots
        self.pattern.signal.changed.connect(self.allow_set_select.update)
        self.pattern.signal.changed.connect(self.pp.update_pattern)
        #  disable mps control if pattern is changed and not applied
        self.pattern.signal.changed.connect(self.allow_set_select.disable)
        #  reenable mps control if pattern is applied
        self.pp._applyB.pressed.connect(self.allow_set_select.enable)
        self.allow_set_select.allowseq_changed.connect(self.stat_table.update)
        self.allow_set_select.class_changed.connect(self.pp.update)
        #  Initialize
#        self.pattern_select.mode_select.setCurrentIndex(0)
#        self.pattern_select.patt_select.setCurrentIndex(0)
#        self.pattern_select._updateCharge()


def main():
    logging.info(QtCore.PYQT_VERSION_STR)
    logging.getLogger().setLevel(logging.DEBUG)

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
