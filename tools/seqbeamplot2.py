import pyqtgraph as pg
import numpy

fixedRates = ['929kHz','71.4kHz','10.2kHz','1.02kHz','102Hz','10.2Hz','1.02Hz']
acRates    = ['60Hz','30Hz','10Hz','5Hz','1Hz','0.5Hz']
f = None
FixedIntvs = [1, 13, 91, 910, 9100, 91000, 910000]

verbose = False

class Engine(object):

    def __init__(self):
        self.request = 0
        self.instr   = 0
        self.frame   = -1
        self.ccnt    = [0]*4

class Instruction(object):

    def __init__(self, args):
        self.args = args

class FixedRateSync(Instruction):

    opcode = 0

    def __init__(self, marker, occ):
        super(FixedRateSync, self).__init__( (self.opcode, marker, occ) )

    def print_(self):
        return 'FixedRateSync({}) # occ({})'.format(fixedRates[self.args[1]],self.args[2])

    def execute(self,engine):
        intv = FixedIntvs[self.args[1]]
        engine.instr += 1
        step = intv*self.args[2]-(engine.frame%intv)
        if step>0:
            engine.frame  += step
            engine.request = 0

class ACRateSync(Instruction):

    opcode = 1

    def __init__(self, timeslotm, marker, occ):
        super(ACRateSync, self).__init__( (self.opcode, timeslotm, marker, occ) )

    def print_(self):
        return 'ACRateSync({}/0x{:x}) # occ({})'.format(acRates[self.args[2]],self.args[1],self.args[3])
    

class Branch(Instruction):

    opcode = 2

    def __init__(self, args):
        super(Branch, self).__init__(args)

    @classmethod
    def unconditional(cls, line):
        return cls((cls.opcode, line))

    @classmethod
    def conditional(cls, line, counter, value):
        return cls((cls.opcode, line, counter, value))

    def print_(self):
        if len(self.args)==2:
            return 'Branch unconditional to line {}'.format(self.args[1])
        else:
            return 'Branch to line {} until ctr{}={}'.format(self.args[1],self.args[2],self.args[3])

    def execute(self,engine):
        if len(self.args)==2:
            engine.instr = self.args[1]
        else:
            if engine.ccnt[self.args[2]]==self.args[3]:
                engine.instr += 1
                engine.ccnt[self.args[2]] = 0
            else:
                engine.instr = self.args[1]
                engine.ccnt[self.args[2]] += 1
    
class BeamRequest(Instruction):

    opcode = 4
    
    def __init__(self, charge):
        super(BeamRequest, self).__init__((self.opcode, charge))

    def print_(self):
        return 'BeamRequest charge {}'.format(self.args[1])

    def execute(self,engine):
        engine.request = (self.args[1]<<16) | 1
        engine.instr += 1

class ControlRequest(Instruction):

    opcode = 5
    
    def __init__(self, word):
        super(ControlRequest, self).__init__((self.opcode, word))

    def print_(self):
        return 'ControlRequest word 0x{:x}'.format(self.args[1])

    def execute(self,engine):
        engine.request = self.args[1]
        engine.instr += 1

class SeqUser:
    def __init__(self, start=0, stop=1000, file='', verbose=False):
        self.start = start
        self.stop  = stop
        self.verbose = verbose

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

    def color(self,dest):
        x = float(dest)/float(self.ndest-1)
        c = (0,0,0)
        if x < 0.5:
            c = (511*(0.5-x),511*x,0)
        else:
            c = (0,511*(1.0-x),511*(x-0.5))
        print('dest {:}  x {:}  color {:}'.format(dest,x,c))
        return c

    def execute(self, seqdict):

        self.app = pg.Qt.QtGui.QApplication([])
        self.win  = pg.GraphicsWindow()

        self.plot  = []
        self.xdata = []
        self.ydata = []
        self.ndest = len(seqdict['allow'])
        for i in range(self.ndest):
            self.xdata.append([])
            self.ydata.append([])

        x = 0

        request_engines = []
        for i in range(len(seqdict['request'])):
            request_engines.append(Engine())

        allow_engines = []
        for i in range(len(seqdict['allow'])):
            allow_engines.append(Engine())

        gframe = -1
        while gframe < self.stop:

            requests  = 0
            allow     = 0
            arequest  = -1

            #  Form allow result first
            for i,engine in enumerate(allow_engines):

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['allow'][i]

                if self.verbose:
                    print('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    if self.verbose:
                        print('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        if self.verbose:
                            print('\tframe: {}  instr {}  request {:x}'.format
                                  (frame,engine.instr,request))
                        if request != 0:
                            allow    |= (1<<i)
                            if frame >= self.start:
                                self.xdata[i].append(frame)
                                self.ydata[i].append(1+i*0.04)
                        frame   = int(engine.frame)
                        request = int(engine.request)

            #  Form request and apply allow table
            for i,engine in enumerate(request_engines):

                frame    = int(engine.frame)
                request  = int(engine.request)
                instrset = seqdict['request'][i]

                if self.verbose:
                    print('Engine {}:  frame {}  request {:x}'.format(i,frame,request))

                while frame == gframe:

                    if self.verbose:
                        print('\t[{}] = {}'.format(engine.instr,instrset[engine.instr]))

                    request  = int(engine.request)
                    instrset[engine.instr].execute(engine)

                    if engine.frame != frame:
                        if self.verbose:
                            print('\tframe: {}  instr {}  request {:x}'.format
                                  (frame,engine.instr,request))
                        if request != 0:
                            requests |= (1<<i)
                            if allow&seqdict['allowmask'][i]==seqdict['allowmask'][i]:
                                arequest  = i
                            if frame >= self.start:
                                self.xdata[i].append(frame)
                                self.ydata[i].append(2+i*0.04)
                        frame   = int(engine.frame)
                        request = int(engine.request)

            if arequest>=0 and gframe >= self.start:
                self.xdata[arequest].append(gframe)
                self.ydata[arequest].append(0+arequest*0.04)

            if self.verbose:
                print('== gframe {}  requests {:x}  request {}'.format(gframe,requests,arequest))
            gframe += 1

        q = self.win.addPlot(title='Destn')
        for i in range(self.ndest):
            q.plot(self.xdata[i],self.ydata[i],pen=None,symbolPen=None,
                   symbolBrush=self.color(i), symbol='s', pxMode=True, size=2)

        self.app.processEvents()

        input('Press ENTER to exit')


