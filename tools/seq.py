#
#  The 'execute' functions below are LCLS2-specific
#
import json

verbose = False
#verbose = True

fixedRates = ['1.02Hz','10.2Hz','102Hz','1.02kHz','10.2kHz','71.4kHz','929kHz']
acRates    = ['0.5Hz','1Hz','5Hz','10Hz','30Hz','60Hz']
FixedIntvs = [910000, 91000, 9100, 910, 91, 13, 1]
ACIntvs    = [120, 60, 12, 6, 2, 1]

class Instruction(object):

    def __init__(self, args):
        self.args = args
        #print(args)

    def encoding(self):
        args = [0]*7
        args[0] = len(self.args)-1
        args[1:len(self.args)+1] = self.args
        return args

class FixedRateSync(Instruction):

    opcode = 0
    FixedIntvsDict = {"1H":{"intv":910000,"marker":0}, "10H":{"intv":91000,"marker":1}, "100H":{"intv":9100,"marker":2}, "1kH":{"intv":910,"marker":3}, "10kH":{"intv":91,"marker":4}, "70kH":{"intv":13,"marker":5}, "910kH":{"intv":1,"marker":6}}

    def __init__(self, marker, occ=0):
        if occ > 0xfff:
            raise ValueError('FixedRateSync called with occ={}'.format(occ))
        self.mk = marker
        markerInt = self.FixedIntvsDict[self.mk]['marker']
        #marker = self.FixedIntvs.index(self.temp)
        super(FixedRateSync, self).__init__( (self.opcode, markerInt, occ) )

    def _word(self):
        return int((2<<29) | ((self.args[1]&0xf)<<16) | (self.args[2]&0xfff))
    
    def _schedule(self):
        return (0<<14) | (self.args[1]&0xf)

    def print_(self):
        return 'FixedRateSync({}) # occ({})'.format(fixedRates[self.args[1]],self.args[2])

    def execute(self,engine):
        intv = self.FixedIntvsDict[self.mk]['intv']
        engine.instr += 1
        step = intv*self.args[2]-(engine.frame%intv)
        if step>0:
            engine.frame  += step
            engine.request = 0
        engine.modes |= 1

class ACRateSync(Instruction):

    ACIntvs    = [1, 2, 6, 12, 60, 120]
    ACIntvsDict = {"0.5H":{"intv":120,"marker":0}, "1H":{"intv":60,"marker":1}, "5H":{"intv":12,"marker":2}, "10H":{"intv":6,"marker":3}, "30H":{"intv":2,"marker":4}, "60H":{"intv":1,"marker":5}}
    opcode = 1

    def __init__(self, timeslotm, marker, occ=0):
        if occ > 0xfff:
            raise ValueError('ACRateSync called with occ={}'.format(occ))
        self.mk = marker
        markerInt = self.ACIntvsDict[self.mk]['marker']
        super(ACRateSync, self).__init__( (self.opcode, timeslotm, markerInt, occ) )

    def _word(self):
        return int((3<<29) | ((self.args[1]&0x3f)<<23) | ((self.args[2]&0xf)<<16) | (self.args[3]&0xfff))

    def _schedule(self):
        return (1<<14) | ((self.args[1]&0x3f)<<3) | (self.marker&0x7)

    def print_(self):
        return 'ACRateSync({}/0x{:x}) # occ({})'.format(acRates[self.args[2]],self.args[1],self.args[3])
    
    def execute(self,engine):
        intv = self.ACIntvsDict[self.mk]['intv']
        #intv = ACIntvs[self.args[2]]
        engine.instr += 1
        mask = self.args[1]&0x3f
#        print('ACRateSync: args {:}  mask {:x}  intv {:}'.format(self.args,mask,intv))
        for i in range(self.args[3]):
            while True:
                engine.acframe += 1
                ts = engine.acframe % 6
#                print('  frame {:}  ts {:}'.format(engine.acframe,ts))
                if ((1<<ts)&mask)!=0 and (int(engine.acframe/6)%intv)==0:
                    break

        engine.request = 0
        engine.modes  |= 2

class Branch(Instruction):

    opcode = 2

    def __init__(self, args):
        super(Branch, self).__init__(args)

    def _word(self, a):
        w = a & 0x7ff
        if len(self.args)>2:
            w = ((self.args[2]&0x3)<<27) | (1<<24) | ((self.args[3]&0xff)<<16) | w
        return int(w)

    @classmethod
    def unconditional(cls, line):
        return cls((cls.opcode, line))

    @classmethod
    def conditional(cls, line, counter, value):
        if value == 0:
            #  sequence_engine_yaml.cc uses test_value to distinguish conditional/unconditional
            raise ValueError('BranchConditional called with value=0, evokes bug in sequence_engine_yaml.cc')
        if value > 0xfff:
            raise ValueError('BranchConditional called with value={}'.format(value))
        return cls((cls.opcode, line, counter, value))

    def address(self):
        return self.args[1]

    def print_(self):
        if len(self.args)==2:
            return 'Branch unconditional to line {}'.format(self.args[1])
        else:
            return 'Branch to line {} until ctr{}={}'.format(self.args[1],self.args[2],self.args[3])

    def execute(self,engine):
        if len(self.args)==2:
            if engine.instr==self.args[1]:  # branch to self
                engine.frame += 1
                engine.done = True
            engine.instr = self.args[1]
        else:
            if engine.ccnt[self.args[2]]==self.args[3]:
                engine.instr += 1
                engine.ccnt[self.args[2]] = 0
            else:
                engine.instr = self.args[1]
                engine.ccnt[self.args[2]] += 1
    
class CheckPoint(Instruction):

    opcode = 3
    
    def __init__(self):
        super(CheckPoint, self).__init__((self.opcode,))

    def _word(self):
        return int((1<<29))

    def print_(self):
        return 'CheckPoint'

    def execute(self,engine):
        engine.instr += 1

class BeamRequest(Instruction):

    opcode = 4
    
    def __init__(self, charge):
        super(BeamRequest, self).__init__((self.opcode, charge))

    def _word(self):
        return int((4<<29) | self.args[1])

    def print_(self):
        return 'BeamRequest charge {}'.format(self.args[1])

    def execute(self,engine):
        engine.request = (self.args[1]<<16) | 1
        engine.instr += 1

class ControlRequest(Instruction):

    opcode = 5
    
    def __init__(self, word):
        super(ControlRequest, self).__init__((self.opcode, word))
 
    def _word(self):
        return int((4<<29) | self.args[1])

    def print_(self):
        return 'ControlRequest word 0x{:x}'.format(self.args[1])

    def execute(self,engine):
        engine.request = self.args[1]
        engine.instr += 1

