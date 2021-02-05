import pyqtgraph as pg
import numpy as np
import json
import argparse

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--file", required=True, help="seqsim data file")
    args = parser.parse_args()

    app  = pg.Qt.QtGui.QApplication([])
    win  = pg.GraphicsWindow()

    data = json.load(open(args.file,mode='r'))

    for row,pattern in enumerate(data):
        title = args.file+' ['
        pc = pattern['pc_by_dest']
        print('pc:',pc)
        for i in range(len(pc.keys())):
            title += '%d,'%pc['%d'%i]
        title += ']'
        q = win.addPlot(title=title,col=0,row=row)

        plotdata = pattern['dest_by_bucket']
        q.plot(plotdata[0],plotdata[1],pen=None,symbolPen=None,
                   #symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)
                   symbol='s', pxMode=True, size=2)

    app.processEvents()

    input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)
