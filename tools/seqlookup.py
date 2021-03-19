def seq_lookup(name):
    d = {'0 Hz'       :['Branch.unconditional(0)'],
         '1 Hz'       :['BeamRequest(0)','FixedRateSync(6,1)','Branch.unconditional(0)'],
         '10 Hz'      :['BeamRequest(0)','FixedRateSync(5,1)','Branch.unconditional(0)'],
         '50 Hz'      :['BeamRequest(0)','FixedRateSync(4,2)','Branch.unconditional(0)'],
         '100 Hz'     :['BeamRequest(0)','FixedRateSync(4,1)','Branch.unconditional(0)'],
         '500 Hz'     :['BeamRequest(0)','FixedRateSync(3,2)','Branch.unconditional(0)'],
         '1 kHz'      :['BeamRequest(0)','FixedRateSync(3,1)','Branch.unconditional(0)'],
         '5 kHz'      :['BeamRequest(0)','FixedRateSync(2,2)','Branch.unconditional(0)'],
         '9.3 kHz'    :['BeamRequest(0)','FixedRateSync(0,100)','Branch.unconditional(0)'],
         '10 kHz'     :['BeamRequest(0)','FixedRateSync(2,1)','Branch.unconditional(0)'],
         '31 kHz'     :['BeamRequest(0)','FixedRateSync(0,30)','Branch.unconditional(0)'],
         '71 kHz'     :['BeamRequest(0)','FixedRateSync(1,1)','Branch.unconditional(0)'],
         '93 kHz'     :['BeamRequest(0)','FixedRateSync(0,10)','Branch.unconditional(0)'],
         '186 kHz'    :['BeamRequest(0)','FixedRateSync(0,5)','Branch.unconditional(0)'],
         '464 kHz'    :['BeamRequest(0)','FixedRateSync(0,2)','Branch.unconditional(0)'],
         '929 kHz'    :['BeamRequest(0)','FixedRateSync(0,1)','Branch.unconditional(0)'],
         '1 Hz off'   :['FixedRateSync(5,5)','BeamRequest(0)','FixedRateSync(5,5)','Branch.unconditional(0)'],
         '10 Hz off'  :['FixedRateSync(4,5)','BeamRequest(0)','FixedRateSync(4,5)','Branch.unconditional(0)'],
         '100 Hz off' :['FixedRateSync(3,5)','BeamRequest(0)','FixedRateSync(3,5)','Branch.unconditional(0)'],
         '1 kHz off'  :['FixedRateSync(2,5)','BeamRequest(0)','FixedRateSync(2,5)','Branch.unconditional(0)'],
         '93 kHz off' :['FixedRateSync(0,5)','BeamRequest(0)','FixedRateSync(0,5)','Branch.unconditional(0)'],
         }

    if name in d:
        instr = ['instrset = []']
        for i in d[name]:
            instr.append('instrset.append({})'.format(i))
        return instr
    else:
        raise ValueError('{} not in seqlookup'.format(name))
