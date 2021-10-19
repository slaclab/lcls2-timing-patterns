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
    parser.add_argument("-o", "--output"            , required=True , help="file output path")
    parser.add_argument("-c", "--control_only"      , action='store_true', help="regenerate control data")
    args = parser.parse_args()

    destn = lcls.lcls_destn()
    pcdef = lcls.lcls_pcdef()

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
            p = {'name':'{}.{}'.format(d['name'],b['name']),
                 'beam':[{'generator':'train','destn':i,
                          'bunch_spacing':b['bunch_spacing'], 'bunches_per_train':b['bunches_per_train'],
                          'start_bucket':0, 'charge':0, 'repeat':False}]}
            #  Set allow sequences. Make last sequence mimic burst pattern for best PC rating
            #  We need a list of allow sequences for each dependent destination
            #  Make them all the same for the bursts
            p['aseq'] = {}
            for a in d['allow']:
                p['aseq'][a] = [{'generator':'lookup', 'name':'0 Hz'},
                                {'generator':'lookup', 'name':'10 Hz'},
                                p['beam'][0]]

            start = b['bunch_spacing'] * (b['bunches_per_train'] - 1)
            p['ctrl'] = [{'seq':1, 'name':'end shutter', 'generator':'train',
                          'destn':1, 'bunch_spacing':1, 'bunches_per_train':1, 'start_bucket':start, 'charge':None, 'repeat':False}]

            #  If we need the kicker, set the standby rate for 1 MHz
            if i>lcls.dumpBSY:  
                p['ctrl'].append({'seq':0, 'generator':'lookup', 'name':'929 kHz', 'request':'ControlRequest(1)'})

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
                    print('seq {}'.format(seq))
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

if __name__=='__main__':
    main()
