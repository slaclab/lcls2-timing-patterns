import argparse
import os
import json
from tools.generators import generator
from tools.seqsim import controlsim
from tools.seqwrite import ctrl_write
#from tools.seq import *

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

    try:
        os.makedirs(args.output)
    except:
        pass

    patterns = [{'name':'mode.pattern'  , 
                 'ctrl':[{'seq':0, 'period':[240]},
                         {'seq':1, 'period':[480]},
                         {'seq':2, 'period':[960]},
                         {'seq':3, 'period':[1920]},
                         {'seq':4, 'period':[3840]},
                         {'seq':5, 'period':[7680]},
                         {'seq':6, 'period':[15360]},
                         {'seq':7, 'period':[30720]},
                         {'seq':8, 'period':[360]},
                         {'seq':9, 'period':[1080]},
                         {'seq':10, 'period':[3240]},
                         {'seq':11, 'period':[9720]},
                         {'seq':12, 'period':[29160]},
                         {'seq':13, 'period':[600]},
                         {'seq':14, 'period':[3000]},
                         {'seq':15, 'period':[15000]}]}]

    destn = {}
    pcdef = {}

    open(args.output+'/destn.json','w').write(json.dumps(destn))
    open(args.output+'/pcdef.json','w').write(json.dumps(pcdef))

    for p in patterns:
        ppath = '{}/{}/'.format(args.output,p['name'])
        try:
            os.mkdir(ppath)
        except:
            pass

        if 'ctrl' in p:
            #  Generate the control sequences
            for b in p['ctrl']:
                b['generator'] = 'periodic'
                b['start_bucket'] = [0]*len(b['period'])
                (name,gen) = generator(b)
                ctrl_write(name=name,
                           instr=gen.instr,
                           output=ppath+'c{}'.format(b['seq']))

        #  Simulate the control requests
        controlsim(pattern='{}/{}'.format(args.output,p['name']),
                   start=0, stop=480000, mode='CW')

if __name__=='__main__':
    main()
