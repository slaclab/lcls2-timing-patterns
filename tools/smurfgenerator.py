
import collections
from shutil import copy
from tools.traingenerator import *
from tools.periodicgenerator import *
from tools.seqsim import *
from tools.seq import *

#  Convert .py to .json file for faster loading
def tojson(fname,d={}):
    cc = {'title'   :'TITLE', 
          'descset' :None, 
          'instrset':None, 
          'crc'     :None}
    exec(compile(open(fname).read(), fname, 'exec'), {}, cc)
    encoding = [len(cc['instrset'])]
    for instr in cc['instrset']:
        encoding = encoding + instr.encoding()

    config = {'title'   :cc['title'],
              'descset' :cc['descset'],
              'encoding':encoding}
    config.update(d)
    ofile = fname.replace('.py','.json')
    open(ofile,mode='w').write(json.dumps(config))

def main():
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("-o", "--output"            , required=True , help="file output path")
    args = parser.parse_args()

    patterns = [{'name':'test'  , 
                 'ctrl':[{'seq':0, 'period':[2**v for v in range(9)]},
                         {'seq':1, 'period':[2**v for v in range(9,11)]},
                         {'seq':2, 'period':[3**v for v in range(1,7)]},
                         {'seq':3, 'period':[5**v for v in range(1,6)]},
                         {'seq':4, 'period':[7**v for v in range(1,4)]},
                          ]}]

    TrainArgs = collections.namedtuple('TrainArgs',['output','train_spacing','trains_per_second','bunch_spacing','bunches_per_train','start_bucket','repeat'])
    targs = {}
    CtrlArgs = collections.namedtuple('PeriodicArgs',['output','period','start_bucket'])
    cargs = {}
    SimArgs = collections.namedtuple('SimArgs',['pattern','start','stop','mode','destn','pcdef'])
    sargs = {}
    for p in patterns:
        ppath = '{}/{}/'.format(args.output,p['name'])
        try:
            os.mkdir(ppath)
        except:
            pass

        if 'ctrl' in p:
            #  Generate the control sequences
            for b in p['ctrl']:
                cargs['output'] = '{}/{}/c{}.py'.format(args.output,p['name'],b['seq'])
                cargs['period'           ] = b['period']
                cargs['start_bucket'     ] = [0]*len(b['period'])
                PeriodicGenerator(CtrlArgs(**cargs))
                tojson(cargs['output'])

        #  Simulate the beam generation/arbitration
        sargs['pattern'] = '{}/{}'.format(args.output,p['name'])
        sargs['start'  ] = 0
        sargs['stop'   ] = 910000
        sargs['mode'   ] = 'CW'
        sargs['destn'  ] = {}
        sargs['pcdef'  ] = []
        seqsim(SimArgs(**sargs))

if __name__=='__main__':
    main()
