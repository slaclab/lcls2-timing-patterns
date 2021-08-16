#  By convention, beam generating sequences are synced to 1Hz at restart
#  Allow sequences may be swapped in at any time, so they may require an extra sync;
#  Put that sync at the end and set the start address in the allow table ('async_start')
#
def seq_lookup(arg):
    d = {'0 Hz'       :{'instr':['Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz'       :{'instr':['BeamRequest(0)','FixedRateSync(6,1)','Branch.unconditional(0)'],
                        'async_start':1},
         '10 Hz'      :{'instr':['BeamRequest(0)','FixedRateSync(5,1)','Branch.unconditional(0)'],
                        'async_start':1},
         '50 Hz'      :{'instr':['BeamRequest(0)','FixedRateSync(4,2)','Branch.unconditional(0)',
                                 'FixedRateSync(5,1)','Branch.unconditional(0)'], 
                        'async_start':3},
         '100 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':1},
         '200 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync(3,5)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '500 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync(3,2)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '1 kHz'      :{'instr':['BeamRequest(0)','FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':1},
         '1.4 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync(1,50)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '5 kHz'      :{'instr':['BeamRequest(0)','FixedRateSync(2,2)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '9.3 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync(0,100)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '10 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync(2,1)','Branch.unconditional(0)'],
                        'async_start':1},
         '46 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync(0,20)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '71 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync(1,1)','Branch.unconditional(0)'],'async_start':1},
         '93 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync(0,10)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '186 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync(0,5)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '464 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync(0,2)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':3},
         '929 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync(0,1)','Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz off'   :{'instr':['FixedRateSync(5,5)','BeamRequest(0)','FixedRateSync(5,5)','Branch.unconditional(0)',
                                 'FixedRateSync(6,1)','Branch.unconditional(0)'],
                        'async_start':4},
         '10 Hz off'  :{'instr':['FixedRateSync(4,5)','BeamRequest(0)','FixedRateSync(4,5)','Branch.unconditional(0)',
                                 'FixedRateSync(5,1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off' :{'instr':['FixedRateSync(3,5)','BeamRequest(0)','FixedRateSync(3,5)','Branch.unconditional(0)',
                                 'FixedRateSync(4,1)','Branch.unconditional(0)'],
                        'async_start':4},
         '1 kHz off'  :{'instr':['FixedRateSync(2,5)','BeamRequest(0)','FixedRateSync(2,5)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':4},
         '93 kHz off' :{'instr':['FixedRateSync(0,5)','BeamRequest(0)','FixedRateSync(0,5)','Branch.unconditional(0)',
                                 'FixedRateSync(3,1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off 0 Hz' :{'instr':['BeamRequest(0)','FixedRateSync(4,1)','Branch.unconditional(0)'],
                            'async_start':1},
         '99 Hz off 1 Hz'  :{'instr':['FixedRateSync(4,1)','BeamRequest(0)','Branch.conditional(0, 0, 98)','FixedRateSync(4,1)','Branch.unconditional(0)',
                                      'FixedRateSync(6,1)','Branch.unconditional(0)'],
                            'async_start':5},
         '90 Hz off 10 Hz' :{'instr':['FixedRateSync(4,1)','BeamRequest(0)','Branch.conditional(0, 0, 8)','FixedRateSync(4,1)','Branch.unconditional(0)', 
                                      'FixedRateSync(5,1)','Branch.unconditional(0)'],
                            'async_start':5},
         '50 Hz off 50 Hz' :{'instr':['FixedRateSync(4,1)','BeamRequest(0)','FixedRateSync(4,1)','Branch.unconditional(0)',
                                      'FixedRateSync(5,1)','Branch.unconditional(0)'],
                            'async_start':4}
         }

    name = arg['name']
    if name in d:
        instr = ['instrset = []']
        for i in d[name]['instr']:
            if 'request' in arg and i=='BeamRequest(0)':
                #  Replace BeamRequest with other request
                i = arg['request']
            instr.append('instrset.append({})'.format(i))
        return {'instr':instr, 'async_start':d[name]['async_start']}
    else:
        raise ValueError('{} not in seqlookup'.format(name))
