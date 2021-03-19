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

def color(idx,nidx):
    x = float(idx)/float(nidx-1)
    c = (0,0,0)
    if x < 0.5:
        c = (511*(0.5-x),511*x,0)
    else:
        c = (0,511*(1.0-x),511*(x-0.5))
    return c

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='simple sequence plotting gui')
    parser.add_argument("--pattern", required=True, help="pattern sub-directory")
    args = parser.parse_args()

    app  = pg.Qt.QtGui.QApplication([])
    win  = pg.GraphicsWindow()
    row = 0

    title = args.pattern+' [dest]'
    q = win.addPlot(title=title,col=0,row=0)
    l = q.addLegend()
    print('legend {}'.format(l.__dict__))
    q.setLabel('left'  ,'Destn')
    q.setLabel('bottom','Bucket')
    data = json.load(open(args.pattern+'/dest.json',mode='r'))
    ipc = 0
    npc = len(data)
    ymax = 0
    ymin = 16
    for pc,pattern in data.items():
        if pc=='allows' or pc=='beams':
            continue
        ymax = np.amax(pattern[1],initial=ymax)
        ymin = np.amin(pattern[1],initial=ymin)
        ay = np.array(pattern[1])+ipc*0.04
        q.plot(pattern[0],ay,pen=None,symbolPen=None,symbolBrush=color(ipc,npc), 
               symbol='s', pxMode=True, size=2, name=pc)
        ipc += 1
    q.setRange(yRange=[ymin,ymax+1])

    title = args.pattern+' [ctrl]'
    q = win.addPlot(title=title,col=0,row=1)
    q.addLegend()
    q.setLabel('left'  ,'SeqBit')
    q.setLabel('bottom','Bucket')
    ctrl = json.load(open(args.pattern+'/ctrl.json',mode='r'))
    ipc = 0
    npc = len(ctrl)
    for seq,pattern in ctrl.items():
        for y,x in pattern.items():
            if len(x) > 0:
                ay = float(y)*np.ones([len(x)])
                q.plot(x,ay,pen=None,symbolPen=None,symbolBrush=color(ipc,18), 
                       symbol='s', pxMode=True, size=2, name='Seq'+seq)
        ipc += 1

    app.processEvents()

    input(bcolors.OKGREEN+'Press ENTER to exit'+bcolors.ENDC)
