from .globals import *

#
#  Simulate trigger logic based on data from simulation output (seqsim.json)
#

class Trigger(object):

    def __init__(self, fixed, ac, ctrl, incl, excl):
        self.fixed = fixed  #  boolean array[7]
        self.ac    = ac     #  .rate,ts boolean arrays[5,6]
        self.ctrl  = ctrl   #  boolean array[18][16]
        self.incl  = incl   #  boolean array[16]
        self.excl  = excl   #  boolean array[16]

    def requires(self):
        v = []
        if self.fixed is not None:
            v.append('fixed')
        if self.ac is not None:
            v.append('ac')
        if self.ctrl is not None:
            v.append('ctrl')
        if self.incl is not None or self.excl is not None:
            v.append('dest')
        return v
        
    def fire(self, fixedrates, acrates, control, dest):
        ratesel = ((self.fixed is not None and fixedrates[self.fixed]) or
                   (self.ac    is not None and acrates(0)[self.ac.rate] and self.ac.ts[acrates(1)]) or
                   (self.ctrl  is not None and control[self.ctrl(0)][self.ctrl(1)]))
        incl    = dest is not None and (self.incl is not None and self.incl[dest])
        excl    = dest is     None or  (self.excl is not None and not self.excl[dest])
        destsel = incl or excl or (self.incl is None and self.excl is None)
        return ratesel and destsel

class ComplTrigger(object):

    def __init__(self, t0, t1):
        self._triggers = (t0,t1)

    def requires(self):
        v = []
        for t in self._triggers:
            v.extend(t.requires())
        return v
        
    #  returns [None,0,1,2(both)]; not interested in AND/OR
    def fire(self, fixedrates, acrates, control, dest):
        v0 = 1 if self._triggers[0].fire(fixedrates, acrates, control, dest) else 0
        v1 = 2 if self._triggers[1].fire(fixedrates, acrates, control, dest) else 0
        return (None,0,1,2)[v0+v1]
    
def triggersim(args):

    trig  = ComplTrigger()
    modes = trig.requires()
    req_fixed = 'fixed' in modes
    req_ac    = 'ac'    in modes
    req_ctrl  = 'ctrl'  in modes
    req_dest  = 'dest'  in modes

    data = json.load(open(args.file,mode='r'))


    for row,pattern in enumerate(data):
        title = args.name+' ['
        pc = pattern['pc_by_dest']
        print('pc:',pc)
        for i in range(len(pc.keys())):
            title += '%d,'%pc['%d'%i]
        title += ']'

        destdata = pattern['dest_by_bucket'] # Destination simulation
        control  = None                      # Control sequence simulation
        next     = 0
        z        = 0
        xdata    = []
        ydata    = []
        for bucket in range(TPGSEC):
            fixedrates = [(bucket%i)==0 for i in FixedIntvs]
            ts         = int(bucket*360/TPGSEC)
            acrates    = ([(int(ts/6)%i)==0 for i in ACIntvs],(ts%6))
            dest       = None
            if bucket==destdata[0][z]:
                dest = destdata[1][z]
                z   += 1
            fire       = trig.fire(fixedrates,acrates,control,dest)
            if fire is not None:
                xdata.append(bucket)
                ydata.append(fire)

        triggers.append({'pc_by_dest':pc.copy(), 'trig_by_bucket':(xdata,ydata)})

    return triggers
                        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='trigger logic plotting gui')
    parser.add_argument("--name" , required=True, help="output name [.json]")
    parser.add_argument("--file" , required=True, help="seqsim source file")
    parser.add_argument("--start", default=  0, type=int, help="beginning timeslot")
    parser.add_argument("--stop" , default=200, type=int, help="ending timeslot")
    parser.add_argument("--mode" , default='CW', help="timeslot mode [CW,AC]")
    parser.add_argument("--trigger", default='', type=str, help="trigger config json")
    args = parser.parse_args()
    
    triggersim(args).show_plots()
