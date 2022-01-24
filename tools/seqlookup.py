#  By convention, beam generating sequences are synced to 1Hz at restart
#  Allow sequences may be swapped in at any time, so they may require an extra sync;
#  Put that sync at the end and set the start address in the allow table ('async_start')
#
#  This is specific to LCLS2 given the translation of markers to time intervals
#
def seq_lookup(arg):
    d = {'0 Hz'       :{'instr':['Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz'       :{'instr':['BeamRequest(0)','FixedRateSync("1H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '10 Hz'      :{'instr':['BeamRequest(0)','FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '50 Hz'      :{'instr':['BeamRequest(0)','FixedRateSync("100H",2)','Branch.unconditional(0)',
                                 'FixedRateSync("10H",1)','Branch.unconditional(0)'], 
                        'async_start':3},
         '100 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '200 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync("1kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '500 Hz'     :{'instr':['BeamRequest(0)','FixedRateSync("1kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '1 kHz'      :{'instr':['BeamRequest(0)','FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '1.4 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync("70kH",50)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '5 kHz'      :{'instr':['BeamRequest(0)','FixedRateSync("10kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '9.3 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync("910kH",100)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '10 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync("10kH",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '46 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync("910kH",20)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '71 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync("70kH",1)','Branch.unconditional(0)'],'async_start':1},
         '93 kHz'     :{'instr':['BeamRequest(0)','FixedRateSync("910kH",10)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '186 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync("910kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '464 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync("910kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '929 kHz'    :{'instr':['BeamRequest(0)','FixedRateSync("910kH",1)','Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz off'   :{'instr':['FixedRateSync("10H",5)','BeamRequest(0)','FixedRateSync("10H",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '10 Hz off'  :{'instr':['FixedRateSync("100H",5)','BeamRequest(0)','FixedRateSync("100H",5)','Branch.unconditional(0)',
                                 'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off' :{'instr':['FixedRateSync("1kH",5)','BeamRequest(0)','FixedRateSync("1kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '1 kHz off'  :{'instr':['FixedRateSync("10kH",5)','BeamRequest(0)','FixedRateSync("10kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '93 kHz off' :{'instr':['FixedRateSync("910kH",5)','BeamRequest(0)','FixedRateSync("910kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off 0 Hz' :{'instr':['BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)'],
                            'async_start':1},
         '99 Hz off 1 Hz'  :{'instr':['FixedRateSync("100H",1)','BeamRequest(0)','Branch.conditional(0, 0, 98)','FixedRateSync("100H",1)','Branch.unconditional(0)',
                                      'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                            'async_start':5},
         '90 Hz off 10 Hz' :{'instr':['FixedRateSync("100H",1)','BeamRequest(0)','Branch.conditional(0, 0, 8)','FixedRateSync("100H",1)','Branch.unconditional(0)', 
                                      'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                            'async_start':5},
         '50 Hz off 50 Hz' :{'instr':['FixedRateSync("100H",1)','BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)',
                                      'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                            'async_start':4},
         '0.5 Hz AC'  :{'instr':['ACRateSync(0,"0.5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz AC'    :{'instr':['ACRateSync(0,"1H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '5 Hz AC'    :{'instr':['ACRateSync(0,"5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '10 Hz AC'   :{'instr':['ACRateSync(0,"10H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '30 Hz AC'   :{'instr':['ACRateSync(0,"30H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '60 Hz AC'   :{'instr':['ACRateSync(0,"60H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         }

    name = arg['name']
    if name in d:
        instr = ['instrset = []']
        for i in d[name]['instr']:
            #  Make custom replacements
            if 'request' in arg and i=='BeamRequest(0)':
                i = arg['request']
            if 'timeslots' in arg and 'ACRateSync(0,' in i:
                i.replace('ACRateSync(0,','ACRateSync({}'.format(arg['timeslots']))
            instr.append('instrset.append({})'.format(i))
        return {'instr':instr, 'async_start':d[name]['async_start']}
    else:
        raise ValueError('{} not in seqlookup'.format(name))
