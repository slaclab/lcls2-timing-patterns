import collections
from tools.traingenerator import *
from tools.seqsim import *

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

#    patterns = [{'name':'2b_100'  , 'destn':0, 'bunch_spacing':100  , 'bunches_per_train':200   , 'repeat':False }]

    TrainArgs = collections.namedtuple('TrainArgs',['output','train_spacing','trains_per_second','bunch_spacing','bunches_per_train','repeat'])
    targs = {}
    SimArgs = collections.namedtuple('SimArgs',['pattern','start','stop','mode'])
    sargs = {}
    for p in patterns:
        try:
            os.mkdir('{}/{}'.format(args.output,p['name']))
        except:
            pass
        targs['output'] = '{}/{}/d{}.py'.format(args.output,p['name'],p['destn'])
        targs['train_spacing'] = 910000
        targs['trains_per_second'] = 1
        targs['bunch_spacing'] = p['bunch_spacing']
        targs['bunches_per_train'] = p['bunches_per_train']
        targs['repeat'] = p['repeat']
        TrainGenerator(TrainArgs(**targs))

        sargs['pattern'] = '{}/{}'.format(args.output,p['name'])
        sargs['start'  ] = 0
        sargs['stop'   ] = 910000  # controls beam.py output
        sargs['mode'   ] = 'CW'
        seqsim(SimArgs(**sargs))

if __name__=='__main__':
    main()
