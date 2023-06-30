#  Make a pattern that includes the hutch sequence as a demonstration
#  of RIX triggering needs
import collections
from shutil import copy
from tools.traingenerator import *
from tools.periodicgenerator import *
from tools.seqsim import seqsim, controlsim
from tools.generators import generator
from tools.seqwrite import beam_write, allow_write, ctrl_write
from tools.trigger import add_triggers
import lcls
import json
from multiprocessing import Pool
import logging
import time
import subprocess

args  = None
destn = lcls.lcls_destn()
pcdef = lcls.lcls_pcdef()

def write_pattern(p):
    ppath = '{}/{}/'.format(args.output,p['name'])
    tbegin = time.perf_counter()
    logging.info(f'Begin {ppath}')

    try:
        os.mkdir(ppath)
    except:
        pass

    #  Generate the beam sequences
    if 'beam' in p:
        for d,b in p['beam'].items():
            (name,gen) = generator(b)
            logging.debug('name [{}]'.format(name))
            beam_write(name=name,
                       instr=gen.instr, 
                       output=ppath+'d{}'.format(d),
                       destn=d,
                       allow=destn[b['destn']]['allow'])

        #  Add required allow tables to pattern (or generate unique ones)
        #  Need to be selective here, else the combinatorics are huge (slow simulation)
        for d,a in p['aseq'].items():
            for i,seq in enumerate(a):
                (name,gen) = generator(seq)
                allow_write(name=name,
                            instr=gen.instr,
                            start=gen.async_start,
                            pcdef=pcdef,
                            output=ppath+'allow_d{}_{}'.format(d,i))

    if 'ctrl' in p:
        #  Generate the control sequences
        for b in p['ctrl']:
            (name,gen) = generator(b)
            ctrl_write(name=name,
                       instr=gen.instr,
                       output=ppath+'c{}'.format(b['seq']),
                       codes=b['codes'])

    if args.control_only:
        #  Simulate the control requests
        controlsim(pattern='{}/{}'.format(args.output,p['name']),
                   start=0, stop=int(TPGSEC*args.simulate), mode='CW')

    else:
        #  Simulate the beam generation/arbitration and control requests
        seqsim(pattern='{}/{}'.format(args.output,p['name']),
               start=0, stop=int(TPGSEC*args.simulate), mode='CW',
               destn_list=destn, pc_list=range(14), seq_list=p['aseq'])

    add_triggers(ppath)

    tend = time.perf_counter()
    logging.info(f'End {ppath}: {tend-tbegin} s')

def create_pattern_2mode(args_time=[0.391,0.005], args_period=[9100000,9100], args_bunch_period=28):
    DUMPSXR = 4

    #  bunches per TPG second
    bunch_rate = TPGSEC//args_bunch_period

    #  readout times translated to number of bunches
    d = {}
    if args_period[0] > args_period[1]:
        d['slow'] = {'period' : args_period[0]//args_bunch_period,
                     'readout': int(args_time[0]*TPGSEC+args_bunch_period-1)//args_bunch_period}
        d['fast'] = {'period' : args_period[1]//args_bunch_period,
                     'readout': int(args_time[1]*TPGSEC+args_bunch_period-1)//args_bunch_period}
    else:
        d['fast'] = {'period' : args_period[0]//args_bunch_period,
                     'readout': int(args_time[0]*TPGSEC+args_bunch_period-1)//args_bunch_period}
        d['slow'] = {'period' : args_period[1]//args_bunch_period,
                     'readout': int(args_time[1]*TPGSEC+args_bunch_period-1)//args_bunch_period}

    print(f'd {d}')
    #  expand the slow gap to be a multiple of the fast period
    n = (d['slow']['readout'] - d['fast']['readout'] + d['fast']['period'] - 1) // d['fast']['period']
    d['slow']['readout'] = n*d['fast']['period']+d['fast']['readout']
    print(f'n {n}  d {d}')

    #  translate arguemnts to buckets
    periodic_args = {'period':[d['slow']['period']*args_bunch_period,
                               d['fast']['period']*args_bunch_period],
                     'start' :[0,0],
                     'repeat':-1,
                     'notify':False}
    print(f'bunch_period {args_bunch_period}  n {n}')
    print(f'periodic_args {periodic_args}')
    train_args = {'start_bucket' :(d['slow']['readout']+1)*args_bunch_period,
                  'train_spacing':d['fast']['period']*args_bunch_period,
                  'bunch_spacing':args_bunch_period,
                  'bunches_per_train':d['fast']['period']-d['fast']['readout'],
                  'repeat':d['slow']['period'] // d['fast']['period'] - n,
                  'notify':False}
    # Added parameters for repeating with a larger structured gap
    train_args['rrepeat'] = True
    train_args['rpad'] = d['slow']['period']*args_bunch_period-train_args['repeat']*train_args['train_spacing']

    print(f'train_args {train_args}')

    rate = TPGSEC//args_bunch_period
    ratename = f'{(rate+500)//1000} kHz'
    bu   = d['fast']['period']-d['fast']['readout']
    p = {'name': '{}.{}_{}'.format('DUMPSXR',d['slow']['period']*args_bunch_period,d['fast']['period']*args_bunch_period),
         'beam': {j:{'generator':'lookup', 'name':'0 Hz' ,'rate':0    , 'destn':j} for j in destn.keys()}}  # initialize all destns to 0 Hz
    # DUMPBSY: 'rate' value is just approx: used for kicker setup
    p['beam'][lcls.dumpBSY] = {'generator':'periodic', 'name':ratename,'rate':rate, 'destn':lcls.dumpBSY, 'charge':0, 'period':args_bunch_period, 'start_bucket':0, 'repeat':-1 }
    # Schedule the same rate to LASER so when the shutter is inserted we can keep stable laser
    p['beam'][0] = p['beam'][lcls.dumpBSY]
    # DUMPSXR : make a train
    p['beam'][DUMPSXR] = {'generator':'train' , 'name':'{}b_{}'.format(bu,args_bunch_period),'rate':rate, 'destn':DUMPSXR, 'charge':0, 
                          'start_bucket'     :train_args['start_bucket'],
                          'bunch_spacing'    :train_args['bunch_spacing'],
                          'bunches_per_train':train_args['bunches_per_train'], 
                          'repeat'           :train_args['repeat'], 
                          'rrepeat'          :train_args['rrepeat'], 
                          'rpad'             :train_args['rpad'], 
                          'train_spacing'    :train_args['train_spacing'] }  

    #  Set allow sequences. Make last sequence mimic beam pattern for best PC rating
    #  We need a list of allow sequences for each dependent destination
    #  Allow sequences are in increasing order of "power"
    p['aseq'] = {j:[{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j}] for j in destn.keys()}  # initialize allow table to one 0 Hz entry
    for a in destn[DUMPSXR]['allow']:
        aseq = []
        if rate> 0:
            aseq.append({'generator':'lookup', 'name':'0 Hz'})
        if rate> 1:
            aseq.append({'generator':'lookup', 'name':'1 Hz'})
        if rate> 10:
            aseq.append({'generator':'lookup', 'name':'10 Hz'})
        if rate> 0:
            aseq.append(p['beam'][a])
            p['aseq'][a] = aseq
        print(f'aseq[{a}] = {aseq}')

    #  If we need the kicker, 
    #    (1) set the standby rate for full rate if pattern >= 10kHz
    #    (2) request the same rate to the DumpBSY
    #    (3) request 1 Hz to the highest priority engine to the DumpBSY
    # Initializing all Exp Sequences (control seq) to 0Hz
    p['ctrl'] = [{'seq':i, 'generator':'lookup', 'name':'0 Hz', 'request':'ControlRequest(1)', 'codes':{j:'None' for j in range(4)}} for i in range (MAXCTL)]
    if rate>=10000:
        p['ctrl'][0]={'seq':0, 'generator':'lookup', 'name':ratename, 'request':'ControlRequest([1])', 'codes':{0:'KeepAlive'}}
    if rate>1000:
        #  Choose to shift BSY_keep by 28 buckets to not disturb diagnostics
        p['beam'][lcls.dumpBSY_keep] = {'generator':'periodic', 'name':'100 Hz', 'destn':lcls.dumpBSY_keep, 'charge':0, 'period':9100,'start_bucket':args_bunch_period, 'repeat':-1}

    # Scheduling BPM Calibration bit - no opportunity

    #BSA Control Bits
    for i in [2,4]:
        def codeset(rates):
            name = destn[i]['name']
            return {j:f'{name} {r}Hz' for j,r in enumerate(rates)}

        #  Offset the 1Hz triggers to find beam beyond the dump
        p['ctrl'][4*(3+i)]={'seq':4*(3+i), 'generator':'periodic', 'name':'1/10/100 Hz', 'codes':codeset([1,10,100]),
                            'charge':None, 'period':[910000,91000,9100], 'start_bucket':[0,0,0],'repeat':-1} 
    if args.control_only:
        del p['aseq']
        del p['beam']

    p['ctrl'][69] = {'seq':69,
                     'codes':{0:'Fast Andor Gated'},
                     'generator':'train' , 'name':'{}b_{}'.format(bu,args_bunch_period),'rate':rate, 'destn':DUMPSXR, 'charge':None, 
                     'start_bucket'     :(n+1)*d['fast']['period']*args_bunch_period,
                     'bunch_spacing'    :train_args['bunch_spacing'],
                     'bunches_per_train':1,
                     'charge'           :None,
                     'repeat'           :d['slow']['period'] // d['fast']['period'] - n,
                     'rrepeat'          :train_args['rrepeat'], 
                     'rpad'             :train_args['rpad'], 
                     'train_spacing'    :train_args['train_spacing'] }  

    #  Add experiment sequences to ctrl[17]
    p['ctrl'][70] = {'seq':70, 'generator':'periodic' , 'name':'Andor', 'charge':None, 
                     'period'      :periodic_args['period'], 
                     'start_bucket':periodic_args['start'], 
                     'repeat'      :periodic_args['repeat'], 
                     'codes'       :{0:'SlowAndor',1:'FastAndor'} }
#    p['ctrl'][71] = {'seq':71, 'generator':'train'    , 'name':'{}b+{}'.format(b['bunches'],b['spacing']), 'charge':None, 'start_bucket':b['start'], 'bunch_spacing':b['spacing'], 'bunches_per_train':b['bunches']+1, 'repeat':args.trains-1, 'train_spacing':b['train_spacing'], 'codes':{0:'BunchTrain'} }  
    p['ctrl'][71] = {'seq':71,
                     'codes':{0:'BunchTrain'},
                     'generator':'train' , 'name':'{}b_{}'.format(bu,args_bunch_period),'rate':rate, 'destn':DUMPSXR, 'charge':0, 
                     'start_bucket'     :train_args['start_bucket'],
                     'bunch_spacing'    :train_args['bunch_spacing'],
                     'bunches_per_train':train_args['bunches_per_train'], 
                     'charge'           :None,
                     'repeat'           :train_args['repeat'], 
                     'rrepeat'          :train_args['rrepeat'], 
                     'rpad'             :train_args['rpad'], 
                     'train_spacing'    :train_args['train_spacing'] }  

    return p

def main():
    global args
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output", required=True , help="file output path")
    parser.add_argument("-n", "--trains", default=1, type=int, help="number of bunch trains")
    parser.add_argument("-s", "--simulate", default=1., type=float, help="simulation time (seconds)")
    parser.add_argument("-c", "--control_only", action='store_true' , help="regenerator cX files only")
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--debug"  , action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    #  Patterns list of dictionaries whose entries are:
    #    'name' : some descriptive identifier
    #    'beam' : list of generators with destination #
    #    'ctrl' : list of generators with sequence #, codes
    #    'aseq' : list of generators for allow sequences
    DUMPSXR = 4
    patterns = []

    periods = [ [910000, 9100], [1820000, 9100], [2730000, 9100]]
    #  try all combinations
    for p in periods:
        p = create_pattern_2mode(args_period=p)
        patterns.append(p)
        
    try:
        os.mkdir(args.output)
    except:
        pass

    open(args.output+'/destn.json','w').write(json.dumps(destn))
    open(args.output+'/pcdef.json','w').write(json.dumps(pcdef))

    if args.debug:
        for p in patterns:
            write_pattern(p)
    else:
        with Pool(processes=None) as pool:
            result = pool.map_async(write_pattern, patterns)
            result.wait()

    # Create a tar.gz file
    subprocess.call('tar -czf '+args.output+'.tar.gz '+args.output,shell=True)

if __name__=='__main__':
    main()
