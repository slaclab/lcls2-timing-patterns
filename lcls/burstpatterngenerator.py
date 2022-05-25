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
                logging.debug('seq {}'.format(seq))
                (name,gen) = generator(seq)
                allow_write(name=name,
                            instr=gen.instr,
                            start=0,     # start is used at reset, repeat=False, 
                            pcdef=pcdef, # keep alignment of periodic and burst
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
        #  Simulate the beam generation/arbitration
        seqsim(pattern='{}/{}'.format(args.output,p['name']),
               start=0, stop=910000, mode='CW',
               destn_list=destn, pc_list=range(14), seq_list=p['aseq'])

    tend = time.perf_counter()
    logging.info(f'End {ppath}: {tend-tbegin} s')
    
def main():
    global args
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output"            , required=True , help="file output path")
    parser.add_argument("-c", "--control_only"      , action='store_true', help="regenerate control data")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    bursts = [ {'name':'1b'      , 'bunch_spacing':1    , 'bunches_per_train':1   },
               {'name':'2b_10000', 'bunch_spacing':10000, 'bunches_per_train':2   },
               {'name':'2b_100'  , 'bunch_spacing':100  , 'bunches_per_train':2   },
               {'name':'2b_1'    , 'bunch_spacing':1    , 'bunches_per_train':2   },
               {'name':'3b_1'    , 'bunch_spacing':1    , 'bunches_per_train':3   },
               {'name':'10b_1'   , 'bunch_spacing':1    , 'bunches_per_train':10  },
               {'name':'20b_1'   , 'bunch_spacing':1    , 'bunches_per_train':20  },
               {'name':'50b_1'   , 'bunch_spacing':1    , 'bunches_per_train':50  },
               {'name':'100b_1'  , 'bunch_spacing':1    , 'bunches_per_train':100 },
               {'name':'200b_1'  , 'bunch_spacing':1    , 'bunches_per_train':200 },
               {'name':'500b_1'  , 'bunch_spacing':1    , 'bunches_per_train':500 },
               {'name':'1000b_1' , 'bunch_spacing':1    , 'bunches_per_train':1000},
               {'name':'2000b_1' , 'bunch_spacing':1    , 'bunches_per_train':2000}, ]
    for i in range(2,21):
        bursts.append( {'name':'100b_{}'.format(i), 'bunch_spacing':i, 'bunches_per_train':100} )

    #  Patterns list of dictionaries whose entries are:
    #    'name' : some descriptive identifier
    #    'beam' : list of generators with destination #
    #    'ctrl' : list of generators with sequence #
    #    'aseq' : list of generators for allow sequences
    patterns = []

    for b in bursts:
        for i,d in destn.items():
            if 'nogen' in d:
                continue
            # When we initialize p, we setup 0Hz for all destinations to clear previous scheduled rates.
            p = {}
            p['name'] = '{}.{}'.format(d['name'],b['name'])
            p['beam'] = {j:{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j} for j in destn.keys()}  # initialize all destns to 0 Hz
            p['ctrl'] = {j:{'generator':'lookup', 'name':'0 Hz','request':'ControlRequest(0)'} for j in range(17)}  # initialize all control sequences to none
            
            #  Now, beam to the targeted destination
            p['beam'][i] = {'generator':'train','destn':i,
                            'bunch_spacing':b['bunch_spacing'], 'bunches_per_train':b['bunches_per_train'],
                            'start_bucket':0, 'charge':0, 'repeat':False}
            #  Set allow sequences. Make last sequence mimic burst pattern for best PC rating
            #  We need a list of allow sequences for each dependent destination
            #  Make them all the same for the bursts
            p['aseq'] = {j:[{'generator':'lookup', 'name':'0 Hz','rate':0, 'destn':j}] for j in destn.keys()}  # initialize allow table to one 0 Hz entry
            for a in d['allow']:
                p['aseq'][a].append({'generator':'lookup', 'name':'10 Hz'})
                p['aseq'][a].append(p['beam'][0])

            start = b['bunch_spacing'] * (b['bunches_per_train'] - 1)
            p['ctrl'] = [{'seq':1, 'name':'end shutter', 'generator':'train',
                          'destn':1, 'bunch_spacing':1, 'bunches_per_train':1, 'start_bucket':start, 'charge':None, 'repeat':False}]

            #  If we need the kicker, set the standby rate for 1 MHz
            if i>lcls.dumpBSY:  
                p['ctrl'].append({'seq':0, 'generator':'lookup', 'name':'929 kHz', 'request':'ControlRequest(1)'})

            # Scheduling BPM Calibration bit:     
             p['ctrl'][1]={'seq':1, 'generator':'lookup', 'name':'100 Hz_skip2', 'request':'ControlRequest(1)'}
            #BSA Control Bits (1Hz)
            if (i>=1 and i<=5):
                p['ctrl'][3+i]={'seq':3+i, 'generator':'lookup', 'name':'1 Hz', 'request':'ControlRequest(7)'}

            if args.control_only:
                del p['beam']
                del p['aseq']
            patterns.append(p)

    try:
        os.mkdir(args.output)
    except:
        pass

    open(args.output+'/destn.json','w').write(json.dumps(destn))
    open(args.output+'/pcdef.json','w').write(json.dumps(pcdef))

    with Pool(processes=None) as pool:
        result = pool.map_async(generate_pattern, patterns)
        result.wait()

if __name__=='__main__':
    main()

