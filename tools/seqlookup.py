#  By convention, beam generating sequences are synced to 1Hz at restart
#  Allow sequences may be swapped in at any time, so they may require an extra sync;
#  Put that sync at the end and set the start address in the allow table ('async_start')
#
#  This is specific to LCLS2 given the translation of markers to time intervals
#
import argparse

def seq_lookup(arg):
    #  Code below assumes soft timeslot is before hard timeslot
    SoftTsm = 1
    HardTsm = 8
    BothTsm = 9
    d = {'0 Hz'       :{'desc':'No rate',
                        'instr':['Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz'       :{'desc':'1 Hz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("1H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '10 Hz'      :{'desc':'10 Hz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '50 Hz'      :{'desc':'50 Hz syncd to 10H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("100H",2)','Branch.unconditional(0)',
                                 'FixedRateSync("10H",1)','Branch.unconditional(0)'], 
                        'async_start':3},
         '100 Hz'     :{'desc':'100 Hz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '200 Hz'     :{'desc':'200 Hz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("1kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '500 Hz'     :{'desc':'500 Hz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("1kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '1 kHz'      :{'desc':'1 kHz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':1},
         '1.4 kHz'    :{'desc':'1.4 kHz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("70kH",50)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '5 kHz'      :{'desc':'5 kHz syncd to 1kH marker',
                        'instr':['BeamRequest(0)','FixedRateSync("10kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '9.3 kHz'    :{'desc':'9.3 kHz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",100)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '10 kHz'     :{'desc':'10 kHz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("10kH",1)','Branch.unconditional(0)'],
                        'async_start':1},
	 '23 kHz'     :{'desc':'23 kHz syncd to 10H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",40)','Branch.unconditional(0)',
                                 'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '33 kHz'     :{'desc':'33 kHz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",28)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '46 kHz'     :{'desc':'46 kHz syncd to 100H marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",20)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '71 kHz'     :{'desc':'71 kHz on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("70kH",1)','Branch.unconditional(0)'],'async_start':1},
         '93 kHz'     :{'desc':'93 kHz syncd to 1kH marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",10)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '186 kHz'    :{'desc':'186 kHz syncd to 1kH marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '464 kHz'    :{'desc':'464 kHz syncd to 1kH marker',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",2)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':3},
         '929 kHz'    :{'desc':'full rate on the mark',
                        'instr':['BeamRequest(0)','FixedRateSync("910kH",1)','Branch.unconditional(0)'],
                        'async_start':0},
         '10 Hz off 3':{'desc':'Off 3',
                        'instr':['FixedRateSync("910kH",3)', 'BeamRequest(0)', 'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':2},
         '100 Hz off 3':{'desc':'Off 3',
                        'instr':['FixedRateSync("910kH",3)', 'BeamRequest(0)', 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':2},
         '1 Hz off'   :{'desc':'1 Hz delayed 5/10H',
                        'instr':['FixedRateSync("10H",5)','BeamRequest(0)','FixedRateSync("10H",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '10 Hz off'  :{'desc':'10 Hz delayed 5/100H',
                        'instr':['FixedRateSync("100H",5)','BeamRequest(0)','FixedRateSync("100H",5)','Branch.unconditional(0)',
                                 'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off' :{'desc':'100 Hz delayed 5/1kH',
                        'instr':['FixedRateSync("1kH",5)','BeamRequest(0)','FixedRateSync("1kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("100H",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '1 kHz off'  :{'desc':'1 kHz delayed 5/10kH',
                        'instr':['FixedRateSync("10kH",5)','BeamRequest(0)','FixedRateSync("10kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '93 kHz off' :{'desc':'93 kHz delayed 5/910kH',
                        'instr':['FixedRateSync("910kH",5)','BeamRequest(0)','FixedRateSync("910kH",5)','Branch.unconditional(0)',
                                 'FixedRateSync("1kH",1)','Branch.unconditional(0)'],
                        'async_start':4},
         '100 Hz off 0 Hz' :{'desc':'100 Hz on the mark',
                             'instr':['BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)'],
                            'async_start':1},
         '99 Hz off 1 Hz'  :{'desc':'100 Hz remove 1H',
                             'instr':['FixedRateSync("100H",1)','BeamRequest(0)','Branch.conditional(0, 0, 98)','FixedRateSync("100H",1)','Branch.unconditional(0)',
                                      'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                            'async_start':5},
         '90 Hz off 10 Hz' :{'desc':'100 Hz remove 10H',
                             'instr':['FixedRateSync("100H",1)','BeamRequest(0)','Branch.conditional(0, 0, 8)','FixedRateSync("100H",1)','Branch.unconditional(0)', 
                                      'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                            'async_start':5},
         '50 Hz off 50 Hz' :{'desc':'100 Hz remove 50H',
                             'instr':['FixedRateSync("100H",1)','BeamRequest(0)','FixedRateSync("100H",1)','Branch.unconditional(0)',
                                      'FixedRateSync("10H",1)','Branch.unconditional(0)'],
                            'async_start':4},
         '0.5 Hz AC'  :{'desc':'0.5 Hz power aligned',
                        'instr':['ACRateSync(0,"0.5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz AC'    :{'desc':'1 Hz power aligned',
                        'instr':['ACRateSync(0,"1H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '5 Hz AC'    :{'desc':'5 Hz power aligned',
                        'instr':['ACRateSync(0,"5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '10 Hz AC'   :{'desc':'10 Hz power aligned',
                        'instr':['ACRateSync(0,"10H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '30 Hz AC'   :{'desc':'30 Hz power aligned',
                        'instr':['ACRateSync(0,"30H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '60 Hz AC'   :{'desc':'60 Hz power aligned',
                        'instr':['ACRateSync(0,"60H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         #  Separate S and H sequences for complementary rates up to 119 Hz
         '120 Hz AC'  :{'desc':'120 Hz power aligned',
                        'instr':[f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz ACS'   :{'desc':'1 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"1H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '5 Hz ACS'   :{'desc':'5 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '10 Hz ACS'  :{'desc':'10 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"10H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '30 Hz ACS'  :{'desc':'30 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"30H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '60 Hz ACS'  :{'desc':'60 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"60H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '90 Hz ACS'  :{'desc':'90 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"30H",1)','BeamRequest(0)',f'ACRateSync({HardTsm},"30H",1)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,1)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '110 Hz ACS' :{'desc':'110 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"10H",1)','BeamRequest(0)',f'ACRateSync({HardTsm},"10H",1)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,9)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '115 Hz ACS' :{'desc':'115 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"5H",1)','BeamRequest(0)',f'ACRateSync({HardTsm},"5H",1)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,21)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '119 Hz ACS' :{'desc':'119 Hz power aligned Soft TS',
                        'instr':[f'ACRateSync({SoftTsm},"1H",1)','BeamRequest(0)',f'ACRateSync({HardTsm},"1H",1)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,117)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '1 Hz ACH'   :{'desc':'1 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({HardTsm},"1H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '5 Hz ACH'   :{'desc':'5 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({HardTsm},"5H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '10 Hz ACH'  :{'desc':'10 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({HardTsm},"10H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '30 Hz ACH'  :{'desc':'30 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({HardTsm},"30H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '60 Hz ACH'  :{'desc':'60 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({HardTsm},"60H",1)','BeamRequest(0)','Branch.unconditional(0)'],
                        'async_start':0},
         '90 Hz ACH'  :{'desc':'90 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({SoftTsm},"30H",1)',f'ACRateSync({HardTsm},"30H",1)','BeamRequest(0)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,1)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '110 Hz ACH' :{'desc':'110 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({SoftTsm},"10H",1)',f'ACRateSync({HardTsm},"10H",1)','BeamRequest(0)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,9)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '115 Hz ACH' :{'desc':'115 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({SoftTsm},"5H",1)',f'ACRateSync({HardTsm},"5H",1)','BeamRequest(0)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,21)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '119 Hz ACH' :{'desc':'119 Hz power aligned Hard TS',
                        'instr':[f'ACRateSync({SoftTsm},"1H",1)',f'ACRateSync({HardTsm},"1H",1)','BeamRequest(0)',
                                 f'ACRateSync({BothTsm},"60H",1)','BeamRequest(0)','Branch.conditional(3,0,117)',
                                 'Branch.unconditional(0)'],
                        'async_start':0},
         '100 Hz_skip2':{'desc':'100 Hz skip 2',
                         'instr':['FixedRateSync("100H",2)','BeamRequest(0)','FixedRateSync("100H",1)','Branch.conditional(1,0,97)','Branch.unconditional(0)',' FixedRateSync("1H",1)', 'Branch.unconditional(0)'], 
                        'async_start':5},
#100Hz LINAC with 90Hz on a destination and 10Hz to another destination
         '1/10/90 Hz' : {'desc':'1/10/90 Hz on control req bits 0/1/2',
                          'instr':['FixedRateSync("100H",1)','ControlRequest(7)', # Not 10Hz fixed rate
                                   'FixedRateSync("100H",1)','ControlRequest(4)','Branch.conditional(line=2,counter=0,value=7)',  # fire 1Hz bit 
                                   'FixedRateSync("100H",2)','ControlRequest(6)','Branch.conditional(line=2,counter=1,value=8)',  # fire 10 bits
                                   'FixedRateSync("100H",1)','ControlRequest(4)','Branch.conditional(line=8,counter=0,value=8)',  # fire 100Hz bit
                                   'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                          'async_start':11},
         '1/10/100 Hz' : {'desc':'1/10/100 Hz on control req bits 2/1/0',
                          'instr':['ControlRequest(7)', # fire 1/10/100Hz bits
                                   'FixedRateSync("100H",1)','ControlRequest(4)','Branch.conditional(line=1,counter=0,value=8)',  # fire 100Hz bit
                                   'FixedRateSync("100H",1)','ControlRequest(6)','Branch.conditional(line=1,counter=1,value=8)',  # fire 10/100Hz bits
                                   'FixedRateSync("100H",1)','ControlRequest(4)','Branch.conditional(line=7,counter=0,value=8)',  # fire 100Hz bit
                                   'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                          'async_start':10},
         '1/10/10 Hz' : {'desc':'1/10/10 Hz on control req bits 2/1/0',
                         'instr':['ControlRequest(7)', # fire 1/10/10Hz bits
                                    'FixedRateSync("10H",1)','ControlRequest(6)','Branch.conditional(1,0,8)', # fire 10Hz bit
                                    'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':4},

         '1/1/1 Hz' : {'desc':'1/1/1 Hz on control req bits 2/1/0',
                       'instr':['ControlRequest(7)',
                                    'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':1},
#  BSA control for AC rates
#  Soft
         '1/10/120 Hz ACS' : {'desc':'1/10/120 Hz AC on control req bits 0/1/2',
                          'instr':[f'ACRateSync({SoftTsm},"1H",1)','ControlRequest(7)', # fire 1/10/120Hz bits
                                   f'ACRateSync({BothTsm},"60H",1)','ControlRequest(4)','Branch.conditional(line=2,counter=0,value=10)',  # fire 120Hz bit
                                   f'ACRateSync({SoftTsm},"60H",1)','ControlRequest(6)','Branch.conditional(line=2,counter=1,value=8)',  # fire 10/120Hz bits
                                   f'ACRateSync({BothTsm},"60H",1)','ControlRequest(4)','Branch.conditional(line=8,counter=0,value=10)',  # fire 120Hz bit
                                   'Branch.unconditional(0)'],
                          'async_start':0},
         '1/10/10 Hz ACS' : {'desc':'1/10/10 Hz on control req bits 0/1/2',
                         'instr':[f'ACRateSync({SoftTsm},"1H",1)','ControlRequest(7)', # fire 1/10/10Hz bits
                                  f'ACRateSync({SoftTsm},"10H",1)','ControlRequest(6)','Branch.conditional(2,0,8)', # fire 10Hz bit
                                  'Branch.unconditional(0)'],
                           'async_start':0},
         '1/1/1 Hz ACS' : {'desc':'1/1/1 Hz on control req bits 2/1/0',
                       'instr':[f'ACRateSync({SoftTsm},"1H",1)','ControlRequest(7)',
                                'Branch.unconditional(0)'],
                           'async_start':0},
#  Hard
         '1/10/120 Hz ACH' : {'desc':'1/10/120 Hz AC on control req bits 0/1/2',
                          'instr':[f'ACRateSync({HardTsm},"1H",1)','ControlRequest(7)', # fire 1/10/120Hz bits
                                   f'ACRateSync({BothTsm},"60H",1)','ControlRequest(4)','Branch.conditional(line=2,counter=0,value=10)',  # fire 120Hz bit
                                   f'ACRateSync({HardTsm},"60H",1)','ControlRequest(6)','Branch.conditional(line=2,counter=1,value=8)',  # fire 10/120Hz bits
                                   f'ACRateSync({BothTsm},"60H",1)','ControlRequest(4)','Branch.conditional(line=8,counter=0,value=10)',  # fire 120Hz bit
                                   'Branch.unconditional(0)'],
                          'async_start':0},
         '1/10/10 Hz ACH' : {'desc':'1/10/10 Hz on control req bits 0/1/2',
                         'instr':[f'ACRateSync({HardTsm},"1H",1)','ControlRequest(7)', # fire 1/10/10Hz bits
                                  f'ACRateSync({HardTsm},"10H",1)','ControlRequest(6)','Branch.conditional(2,0,8)', # fire 10Hz bit
                                  'Branch.unconditional(0)'],
                           'async_start':0},
         '1/1/1 Hz ACH' : {'desc':'1/1/1 Hz on control req bits 2/1/0',
                       'instr':[f'ACRateSync({HardTsm},"1H",1)','ControlRequest(7)',
                                'Branch.unconditional(0)'],
                           'async_start':0},
#
         '30 Hz SimAC' : {'desc':'30 Hz power align emulation',
                          'instr':['BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",584)',
                                   'FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",584)',
                                   'FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",584)',
                                   'FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",584)',
                                   'Branch.unconditional(0)',
                                   'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':16},
         '90 Hz SimAC' : {'desc':'90 Hz power align emulation',
                          'instr':['FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",584)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",584)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'FixedRateSync("70kH",584)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",583)',
                                   'BeamRequest(0)','FixedRateSync("70kH",584)',
                                   'Branch.unconditional(0)',
                                   'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':22},
         '10 Hz SimAC' : {'desc':'10 Hz power align emulation',
                          'instr':['BeamRequest(0)','FixedRateSync("70kH",4*(583*2+584))',
                                   'Branch.unconditional(0)',
                                   'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':3},
         '110 Hz SimAC' : {'desc':'110 Hz power align emulation',
                           'instr':['FixedRateSync("70kH",583)',
                                    'BeamRequest(0)','FixedRateSync("70kH",583)',
                                    'BeamRequest(0)','FixedRateSync("70kH",584)',
                                    'BeamRequest(0)','FixedRateSync("70kH",583)',
                                    'BeamRequest(0)','FixedRateSync("70kH",583)',
                                    'BeamRequest(0)','FixedRateSync("70kH",584)',
                                    'Branch.conditional(line=5, counter=0, 2)',
                                    'Branch.conditional(line=0, counter=1, 9)',
                                    'Branch.unconditional(0)',
                                    'FixedRateSync("1H",1)','Branch.unconditional(0)'],
                           'async_start':14},
         }

    name = arg['name']
    if name in d:
        instr = ['instrset = []']
        for i in d[name]['instr']:
            #  Make custom replacements
            if 'request' in arg and i=='BeamRequest(0)':
                i = arg['request']
            if 'timeslots' in arg and 'ACRateSync(0,' in i:
                i = i.replace('ACRateSync(0,','ACRateSync({},'.format(arg['timeslots']))
            instr.append('instrset.append({})'.format(i))
        return {'instr':instr, 'async_start':d[name]['async_start']}
    else:
        print('{:16.16s} : {:s}'.format('Name','Description'))
        for k,v in d.items():
             print('{:16.16s} : {}'.format(k,v['desc']))
        raise ValueError('{} not in seqlookup ({})'.format(name,d.keys()))

def main():
    parser = argparse.ArgumentParser(description='Sequence lookup')
    parser.add_argument("--name", type=str, default=None,
                        help="name of sequence")
    args = parser.parse_args()
    gen = seq_lookup({'name':args.name})
    print('{} instructions'.format(gen.ninstr))
    for i in gen.instr:
        print('{}\n'.format(i))

if __name__ == '__main__':
    main()
