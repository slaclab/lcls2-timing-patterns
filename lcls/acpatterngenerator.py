#
#  Outstanding issues:
#   (1)  Should BPMs calibration for any beam rate on Laser destination?
#   (2)  Simulation gives 119Hz diagnostic trigger for */120Hz
#        Diagnostic triggers start at TS=4 (Hard)
#   (3)  For dest HXR+, dumpBsy gets 1Hz trigger, diagnostics fire on it
#   (4)  Same for 10Hz trigger when beam rate > 10
#
import collections
from shutil import copy
from tools.traingenerator import *
from tools.periodicgenerator import *
from tools.seqsim import seqsim, controlsim
from tools.generators import generator
from tools.seqwrite import beam_write, allow_write, ctrl_write
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
                       destn=b['destn'],
                       allow=destn[b['destn']]['allow'],
                       mode='AC')

        #  Add required allow tables to pattern (or generate unique ones)
        #  Need to be selective here, else the combinatorics are huge (slow simulation)
        for d,a in p['aseq'].items():
            for i,seq in enumerate(a):
                (name,gen) = generator(seq)
                allow_write(name=name,
                            instr=gen.instr,
                            start=gen.async_start,
                            pcdef=pcdef,
                            output=ppath+'allow_d{}_{}'.format(d,i),
                            mode='AC')

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
                   start=0, stop=910000, mode='AC')

    else:
        #  Simulate the beam generation/arbitration and control requests
        seqsim(pattern='{}/{}'.format(args.output,p['name']),
               start=0, stop=910000, mode='AC',
               destn_list=destn, pc_list=range(14), seq_list=p['aseq'])

    tend = time.perf_counter()
    logging.info(f'End {ppath}: {tend-tbegin} s')

def main():
    global args
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output", required=True , help="file output path")
    parser.add_argument("-c", "--control_only", action='store_true' , help="regenerator cX files only")
    parser.add_argument("--serial", action='store_true')
    parser.add_argument("--verbose", action='store_true')
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

    #  'rate' value is just approx: used for kicker setup
    rates = [ {'name':'0 Hz'      , 'rate':0},
              {'name':'1 Hz ACH'   , 'rate':1},
              {'name':'10 Hz ACH'  , 'rate':10},
              {'name':'30 Hz ACH'  , 'rate':30},
              {'name':'60 Hz ACH'  , 'rate':60},
              {'name':'90 Hz ACH'  , 'rate':90},
              {'name':'110 Hz ACH' , 'rate':110},
              {'name':'119 Hz ACH' , 'rate':119},
              {'name':'120 Hz AC'  , 'rate':120},]

    for b in rates:
        for i,d in destn.items():
            if 'nogen' in d:
                continue
            # When we initialize p, we setup 0Hz for all destinations to clear previous scheduled rates.
            # p = {'name':'{}.{}'.format(d['name'],b['name']),
            #      'beam':[{'destn':j, 'generator':'lookup', 'name':'0 Hz'} for j in range (15)]}
            # p['beam'][i]={'generator':'lookup', 'name':b['name'], 'destn':i}
            #From Matt's code:
            p = {}
            p['name'] = '{}.{}'.format(d['name'],b['name'])
            p['beam'] = {j:{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j} for j in destn.keys()}  # initialize all destns to 0 Hz
            p['beam'][i] = {'generator':'lookup', 'name':b['name'],'rate':b['rate'], 'destn':i}
            if(i==2):
              p['beam'][0] = {'generator':'lookup', 'name':b['name'],'rate':b['rate'], 'destn':0}#Schedule the same rate to LASER so when the shutter is inserted we can keep stable laser
            #  Set allow sequences. Make last sequence mimic beam pattern for best PC rating
            #  We need a list of allow sequences for each dependent destination
            #  Make them all the same for the bursts
            #  Allow sequences are in increasing order of "power"
            p['aseq'] = {j:[{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j}] for j in destn.keys()}  # initialize allow table to one 0 Hz entry
            for a in d['allow']:
                aseq = []
                if b['rate']> 0:
                    aseq.append({'generator':'lookup', 'name':'0 Hz'})
                if b['rate']> 1:
                    aseq.append({'generator':'lookup', 'name':'1 Hz ACH'})
                if b['rate']> 10:
                    aseq.append({'generator':'lookup', 'name':'10 Hz ACH'})
                if b['rate']> 0:
                    aseq.append(p['beam'][i])
                    p['aseq'][a] = aseq
            #  If we need the kicker, 
            #    (1) set the standby rate for full rate if pattern >= 10kHz
            #    (2) request the same rate to the DumpBSY
            #    (3) request 1 Hz to the highest priority engine to the DumpBSY
	    # Initializing all Exp Sequences (control seq) to 0Hz
            p['ctrl'] = [{'seq':i, 'generator':'lookup', 'name':'0 Hz', 'request':'ControlRequest(1)'} for i in range(MAXCTL)]
            if i>lcls.dumpBSY:
                 dump = p['beam'][0].copy()
                 dump['destn'] = lcls.dumpBSY  # "DumpBSY"
                 p['beam'][lcls.dumpBSY] = dump
                 if b['rate']>10:
                   p['beam'][lcls.dumpBSY_keep] = {'generator':'lookup', 'name':'10 Hz ACH', 'destn':lcls.dumpBSY}
                 else:
                   p['beam'][lcls.dumpBSY_keep] = {'generator':'lookup', 'name':'1 Hz ACH', 'destn':lcls.dumpBSY}

            # Scheduling BPM Calibration bit:     
            if b['rate']<=60:
                p['ctrl'][1]={'seq':1, 'generator':'lookup', 'name':'60 Hz ACS', 'request':'ControlRequest(1)'}
            #BSA Control Bits
#Diag0       
            if ((i>=1) and (i<=5)):
#1Hz
                if b['rate']>=1:
                    p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/1/1 Hz ACH'}
#10Hz
                if b['rate']>=10:
                    p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/10/10 Hz ACH'}
#100Hz
                if b['rate']>=120:
                    p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1/10/120 Hz ACH'}

                
            if args.control_only:
                del p['aseq']
                del p['beam']
            patterns.append(p)

    try:
        os.mkdir(args.output)
    except:
        pass

    open(args.output+'/destn.json','w').write(json.dumps(destn))
    open(args.output+'/pcdef.json','w').write(json.dumps(pcdef))

    if args.serial:
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
