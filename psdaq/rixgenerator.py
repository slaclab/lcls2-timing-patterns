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

def generate_pattern(p):
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
                       output=ppath+'c{}'.format(b['seq']))

    if args.control_only:
        #  Simulate the control requests
        controlsim(pattern='{}/{}'.format(args.output,p['name']),
                   start=0, stop=910000, mode='CW')

    else:
        #  Simulate the beam generation/arbitration and control requests
        seqsim(pattern='{}/{}'.format(args.output,p['name']),
               start=0, stop=910000, mode='CW',
               destn_list=destn, pc_list=range(14), seq_list=p['aseq'])

    add_triggers(ppath)

    tend = time.perf_counter()
    logging.info(f'End {ppath}: {tend-tbegin} s')

def main():
    global args
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output", required=True , help="file output path")
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
    #    'ctrl' : list of generators with sequence #
    #    'aseq' : list of generators for allow sequences
    patterns = []

    DUMPSXR = 4
    b = {'rate':32500,'name':'33 kHz','bunches':32000,'spacing':28}
    p = {'name': '{}.{}'.format('DUMPSXR','32000b_28'),
         'beam': {j:{'generator':'lookup', 'name':'0 Hz' ,'rate':0    , 'destn':j} for j in destn.keys()}}  # initialize all destns to 0 Hz
    # DUMPBSY: 'rate' value is just approx: used for kicker setup
    p['beam'][lcls.dumpBSY] = {'generator':'lookup', 'name':'33 kHz'  ,'rate':b['rate'], 'destn':lcls.dumpBSY}
    # Schedule the same rate to LASER so when the shutter is inserted we can keep stable laser
    p['beam'][0] = p['beam'][lcls.dumpBSY]
    # DUMPSXR : make a train
    p['beam'][DUMPSXR] = {'generator':'train' , 'name':'{}b_{}'.format(b['bunches'],b['spacing']),'rate':b['rate'], 'destn':DUMPSXR, 'charge':0, 'start_bucket':0, 'bunch_spacing':b['spacing'], 'bunches_per_train':b['bunches'], 'repeat':False }  

    #  Set allow sequences. Make last sequence mimic beam pattern for best PC rating
    #  We need a list of allow sequences for each dependent destination
    #  Allow sequences are in increasing order of "power"
    p['aseq'] = {j:[{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j}] for j in destn.keys()}  # initialize allow table to one 0 Hz entry
    for a in destn[DUMPSXR]['allow']:
        aseq = []
        if b['rate']> 0:
            aseq.append({'generator':'lookup', 'name':'0 Hz'})
        if b['rate']> 1:
            aseq.append({'generator':'lookup', 'name':'1 Hz'})
        if b['rate']> 10:
            aseq.append({'generator':'lookup', 'name':'10 Hz'})
        if b['rate']> 0:
            aseq.append(p['beam'][a])
            p['aseq'][a] = aseq
        print(f'aseq[{a}] = {aseq}')

        #  If we need the kicker, 
        #    (1) set the standby rate for full rate if pattern >= 10kHz
        #    (2) request the same rate to the DumpBSY
        #    (3) request 1 Hz to the highest priority engine to the DumpBSY
        # Initializing all Exp Sequences (control seq) to 0Hz
        p['ctrl'] = [{'seq':i, 'generator':'lookup', 'name':'0 Hz', 'request':'ControlRequest(1)'} for i in range (18)]
        if b['rate']>=10000:
            p['ctrl'][0]={'seq':0, 'generator':'lookup', 'name':b['name'], 'request':'ControlRequest(2)'}
        if b['rate']>1000:
            #  Choose to shift BSY_keep by 28 buckets to not disturb diagnostics
            p['beam'][lcls.dumpBSY_keep] = {'generator':'periodic', 'name':'100 Hz', 'destn':lcls.dumpBSY_keep, 'charge':0, 'period':9100,'start_bucket':9072}

        # Scheduling BPM Calibration bit - no opportunity

        #BSA Control Bits
#Diag0       
        for i in [2,4]:
#1Hz
            if b['rate']>=1:
                p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/1/1 Hz'}
#10Hz
            if b['rate']>=10:
              p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/10/10 Hz'}
#100Hz
            if b['rate']>=100:
              p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/10/100 Hz'}

            if args.control_only:
                del p['aseq']
                del p['beam']

        #  Add experiment sequences to ctrl[17]
        p['ctrl'][17] = {'seq':17, 'generator':'periodic' , 'name':'1/100 Hz', 'charge':None, 'period':[910000,9100], 'start_bucket':[0,0] }

        patterns.append(p)
        
    try:
        os.mkdir(args.output)
    except:
        pass

    open(args.output+'/destn.json','w').write(json.dumps(destn))
    open(args.output+'/pcdef.json','w').write(json.dumps(pcdef))

    if args.debug:
        for p in patterns:
            generate_pattern(p)
    else:
        with Pool(processes=None) as pool:
            result = pool.map_async(generate_pattern, patterns)
            result.wait()

    # Create a tar.gz file
    subprocess.call('tar -czf '+args.output+'.tar.gz '+args.output,shell=True)

if __name__=='__main__':
    main()
