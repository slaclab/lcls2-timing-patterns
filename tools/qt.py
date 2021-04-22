from PyQt5 import QtCore, QtGui, QtWidgets
from tools.pattern import Pattern
import glob
import os

class PatternSignal(QtCore.QObject):
    changed = QtCore.pyqtSignal(str, name='changed')

    def __init__(self):
        super(PatternSignal,self).__init__()

class PatternQt(Pattern):

    def __init__(self,path):
        super(PatternQt,self).__init__(path)
        self.signal = PatternSignal()

    def update(self, pattern_name):
        super(PatternQt,self).update(pattern_name)
        if self.charge:
            self.signal.changed.emit(self.path)

    def chargeUpdate(self, charge):
        super(PatternQt,self).chargeUpdate(charge)
        if self.path:
            self.signal.changed.emit(self.path)


class LineEditLabel(QtWidgets.QWidget):
    def __init__(self, initValue='1', headLabel='', tailLabel=''):
        super(LineEditLabel,self).__init__()
        self.edit = QtWidgets.QLineEdit(initValue)
        self.edit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.edit.setValidator(QtGui.QIntValidator(1,65535))
        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QLabel(headLabel))
        h.addWidget(self.edit)
        h.addWidget(QtWidgets.QLabel(tailLabel))
        self.setLayout(h)


class PatternSelectionQt(QtWidgets.QGroupBox):

    patternChanged = QtCore.pyqtSignal(str, name='patternChanged')
    chargeChanged  = QtCore.pyqtSignal(int, name='chargeChanged')

    def __init__(self, path, pattern):
        super(PatternSelectionQt,self).__init__('Pattern Select')
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
       

class AllowSetSelectionQt(QtWidgets.QGroupBox):

    allowseq_changed = QtCore.pyqtSignal(str, name='allowseq_changed')
    class_changed    = QtCore.pyqtSignal(dict, name='class_changed')

    def __init__(self,pattern):
        super(AllowSetSelectionQt,self).__init__('Beam Class Set')
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


    def disable(self):
        for b in self.bgroups.values():
            b.setEnabled(False)

    def enable(self):
        for b in self.bgroups.values():
            b.setEnabled(True)

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


def toIntList(l):
    lq = l.strip('[(,').rstrip(')],')
    return [int(i) for i in lq.split(',')]


class StatisticsTableQt(QtWidgets.QGroupBox):
    def __init__(self, pattern):
        super(StatisticsTableQt,self).__init__('Statistics')
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

