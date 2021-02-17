import collections
from shutil import copy
from tools.traingenerator import *
from tools.periodicgenerator import *
from tools.seqsim import *
from tools.seq import *
from tools.destn import *
from tools.pcdef import *

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

    patterns = [ {'name':'1b'      , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':1   , 'repeat':False },
                 {'name':'2b_10000', 'destn':0, 'bunch_spacing':10000, 'bunches_per_train':2   , 'repeat':False },
                 {'name':'2b_100'  , 'destn':0, 'bunch_spacing':100  , 'bunches_per_train':2   , 'repeat':False },
                 {'name':'2b_1'    , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':2   , 'repeat':False },
                 {'name':'3b_1'    , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':3   , 'repeat':False },
                 {'name':'10b_1'   , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':10  , 'repeat':False },
                 {'name':'20b_1'   , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':20  , 'repeat':False },
                 {'name':'50b_1'   , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':50  , 'repeat':False },
                 {'name':'100b_1'  , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':100 , 'repeat':False },
                 {'name':'200b_1'  , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':200 , 'repeat':False },
                 {'name':'500b_1'  , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':500 , 'repeat':False },
                 {'name':'1000b_1' , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':1000, 'repeat':False },
                 {'name':'2000b_1' , 'destn':0, 'bunch_spacing':1    , 'bunches_per_train':2000, 'repeat':False }, ]
    for i in range(2,21):
        patterns.append( {'name':'100b_{}'.format(i), 'destn':0, 'bunch_spacing':i, 'bunches_per_train':100, 'repeat':False } )

    #  New format (multiple destinations, control seq, start bucket,)
    patterns = [{'name':'2b_100'  , 
                 'beam':[{'destn':0, 'bunch_spacing':100  , 'bunches_per_train':200   , 'start_bucket':0, 'repeat':False }],
                 'ctrl':[{'seq':0, 'period':100, 'start_bucket':0 }]}]

    TrainArgs = collections.namedtuple('TrainArgs',['output','train_spacing','trains_per_second','bunch_spacing','bunches_per_train','start_bucket','repeat'])
    targs = {}
    CtrlArgs = collections.namedtuple('PeriodicArgs',['output','period','start_bucket'])
    cargs = {}
    SimArgs = collections.namedtuple('SimArgs',['pattern','start','stop','mode'])
    sargs = {}
    for p in patterns:
        ppath = '{}/{}/'.format(args.output,p['name'])
        try:
            os.mkdir(ppath)
        except:
            pass

        #  Generate the beam train sequences ("regular bunch trains")
        if 'beam' in p:
            allow = []
            for b in p['beam']:
                targs['output'] = ppath+'d{}.py'.format(b['destn'])
                targs['train_spacing'    ] = 910000
                targs['trains_per_second'] = 1
                targs['bunch_spacing'    ] = b['bunch_spacing']
                targs['bunches_per_train'] = b['bunches_per_train']
                targs['start_bucket'     ] = b['start_bucket']
                targs['repeat'           ] = b['repeat']
                TrainGenerator(TrainArgs(**targs))
                #  Copy the allow mask to the pattern
                tojson(targs['output'],{'allow':destn[b['destn']]['allow']})

                span = (targs['train_spacing']*(1-targs['trains_per_second']) +
                        targs['bunch_spacing']*(targs['bunches_per_train']-1) +
                        targs['start_bucket'])
                if span > 910000:
                    print('Bunch train spans the 1Hz marker.  Validation may not match.')
                    print('Extending the validation simulation to the next 1-second interval')
                    print('  may be necessary.')

                allow.extend(destn[b['destn']]['allow'])

            #  Add required allow tables to pattern
            for a in set(allow):
                for pc in range(len(pcdef)):
                    fname = 'allow_d{}_pc{}.py'.format(a,pc)
                    copy('defaults/'+fname,ppath+fname)
                    fname = 'allow_d{}_pc{}.json'.format(a,pc)
                    copy('defaults/'+fname,ppath+fname)

        if 'ctrl' in p:
            #  Generate the control sequences
            for b in p['ctrl']:
                cargs['output'] = '{}/{}/c{}.py'.format(args.output,p['name'],b['seq'])
                cargs['period'           ] = [b['period']]
                cargs['start_bucket'     ] = [b['start_bucket']]
                PeriodicGenerator(CtrlArgs(**cargs))
                tojson(cargs['output'])

        #  Simulate the beam generation/arbitration
        sargs['pattern'] = '{}/{}'.format(args.output,p['name'])
        sargs['start'  ] = 0
        sargs['stop'   ] = 910000
        sargs['mode'   ] = 'CW'
        seqsim(SimArgs(**sargs))

if __name__=='__main__':
    main()
