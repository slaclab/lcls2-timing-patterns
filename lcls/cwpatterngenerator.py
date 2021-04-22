import collections
from shutil import copy
from tools.traingenerator import *
from tools.periodicgenerator import *
from tools.seqsim import seqsim, controlsim
from tools.generators import generator
from tools.seqwrite import beam_write, allow_write, ctrl_write
import lcls
import json

def main():
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output", required=True , help="file output path")
    parser.add_argument("-c", "--control_only", action='store_true' , help="regenerator cX files only")
    args = parser.parse_args()

    destn = lcls.lcls_destn()
    pcdef = lcls.lcls_pcdef()

    #  Patterns list of dictionaries whose entries are:
    #    'name' : some descriptive identifier
    #    'beam' : list of generators with destination #
    #    'ctrl' : list of generators with sequence #
    #    'aseq' : list of generators for allow sequences
    patterns = []

    #  'rate' value is just approx: used for kicker setup
    rates = [ {'name':'0 Hz'   , 'rate':0 },
              {'name':'1 Hz'   , 'rate':1},
              {'name':'10 Hz'  , 'rate':10},
              {'name':'50 Hz'  , 'rate':50},
              {'name':'100 Hz' , 'rate':100},
              {'name':'200 Hz' , 'rate':200},
              {'name':'500 Hz' , 'rate':500},
              {'name':'1 kHz'  , 'rate':1000},
              {'name':'1.4 kHz', 'rate':1400},
              {'name':'5 kHz'  , 'rate':5000},
              {'name':'10 kHz' , 'rate':10000},
              {'name':'46 kHz' , 'rate':45500},
              {'name':'93 kHz' , 'rate':91000},
              {'name':'464 kHz', 'rate':455000},
              {'name':'929 kHz', 'rate':910000}, ]

    for b in rates:
        for i,d in destn.items():
            if 'nogen' in d:
                continue
            p = {'name':'{}.{}'.format(d['name'],b['name']),
                 'beam':[{'generator':'lookup', 'name':b['name'], 'destn':i}]}
            #  Set allow sequences. Make last sequence mimic beam pattern for best PC rating
            #  We need a list of allow sequences for each dependent destination
            #  Make them all the same for the bursts
            #  Allow sequences are in increasing order of "power"
            p['aseq'] = {}
            for a in d['allow']:
                aseq = []
                if b['rate']> 0:
                    aseq.append({'generator':'lookup', 'name':'0 Hz'})
                if b['rate']> 1:
                    aseq.append({'generator':'lookup', 'name':'1 Hz'})
                if b['rate']> 10:
                    aseq.append({'generator':'lookup', 'name':'10 Hz'})
                aseq.append(p['beam'][0])
                p['aseq'][a] = aseq
            #  If we need the kicker, 
            #    (1) set the standby rate for full rate if pattern >= 10kHz
            #    (2) request the same rate to the DumpBSY
            #    (3) request 1 Hz to the highest priority engine to the DumpBSY
            if i>lcls.dumpBSY:
                 if b['rate']>=10000:
                     p['ctrl'] = [{'seq':0, 'generator':'lookup', 'name':'929 kHz', 'request':'ControlRequest(1)'}]
                 dump = p['beam'][0].copy()
                 dump['destn'] = lcls.dumpBSY  # "DumpBSY"
                 p['beam'].append( dump )
                 p['beam'].append( {'generator':'lookup', 'name':'1 Hz', 'destn':lcls.dumpBSY_keep} )

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
    
    for p in patterns:
        ppath = '{}/{}/'.format(args.output,p['name'])
        try:
            os.mkdir(ppath)
        except:
            pass

        #  Generate the beam sequences
        if 'beam' in p:
            for b in p['beam']:
                (name,gen) = generator(b)
                print('name [{}]'.format(name))
                beam_write(name=name,
                           instr=gen.instr, 
                           output=ppath+'d{}'.format(b['destn']), 
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
            #  Simulate the beam generation/arbitration and conctrol requests
            seqsim(pattern='{}/{}'.format(args.output,p['name']),
                   start=0, stop=910000, mode='CW',
                   destn_list=destn, pc_list=range(14), seq_list=p['aseq'])

if __name__=='__main__':
    main()
