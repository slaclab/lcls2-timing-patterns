from tools.seqsim    import allowsim
from tools.seq       import *

import json

def seq_write_py(instr, output):
    #  Write the python file for direct programming
    fname = output+'.py'
    f = open(fname,'w')
    f.write('from tools.seq import *\n')
    f.write('\n')
    for i in instr:
        f.write('{}\n'.format(i))
    f.close()

def seq_write_json(name, output, start=None, allow=None, pcdef=None):
    #  Read the python file for instructions
    fname = output+'.py'
    f = open(fname,'r')
    config = {'title':name, 'descset':None, 'instrset':None, 'pcQmax':None, 'crc':None }
    exec(compile(f.read(), fname, 'exec'), {}, config)
    f.close()

    if pcdef is not None and start is None:
        start = len(config['instrset'])
        #  Append a synchronization command
        print('Appending synchronization command for {} {}'.format(name, output))
        config['instrset'].append(FixedRateSync("1H",1))
        config['instrset'].append(Branch.unconditional(0))

    encoding = [len(config['instrset'])]
    for instr in config['instrset']:
        encoding = encoding + instr.encoding()

    #  Populate a new dictionary with only the fields we want
    cc = {'title'   :name,
          'descset' :None,
          'encoding':encoding}

    if allow is not None:
        cc['allow'] = allow
    if pcdef is not None:
        cc['maxQ'] = allowsim(config['instrset'], encoding, pcdef)
        if start is not None:
            cc['start'] = start

    open(output+'.json','w').write(json.dumps(cc))

def seq_write(name, instr, output, start=None, allow=None, pcdef=None):
    seq_write_py  (instr, output)
    seq_write_json(name, output, start, allow, pcdef)

def beam_write(name, instr, output, allow):
    seq_write(name=name, instr=instr, output=output, allow=allow)

def ctrl_write(name, instr, output):
    seq_write(name=name, instr=instr, output=output)

def allow_write(name, instr, start, pcdef, output):
    seq_write(name=name, instr=instr, start=start, pcdef=pcdef, output=output)
