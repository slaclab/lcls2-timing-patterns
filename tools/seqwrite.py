from tools.seqsim    import allowsim
from tools.seq       import *

import json

def seq_write_py(instr, output, codes=None):
    #  Write the python file for direct programming
    fname = output+'.py'
    f = open(fname,'w')
    f.write('from tools.seq import *\n')
    f.write('\n')
    for i in instr:
        f.write('{}\n'.format(i))
    if codes is not None:
        f.write('codes = {')
        for k,v in codes:
            f.write(f'{k}:{v},')
        f.write('}\n')
    f.close()

def seq_write_json(name, output, start=None, destn=None, allow=None, pcdef=None, mode='CW'):
    #  Read the python file for instructions
    fname = output+'.py'
    f = open(fname,'r')
    config = {'title':name, 'descset':None, 'instrset':None, 'pcQmax':None, 'crc':None, 'codes':None }
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
          'encoding':encoding,
          'codes'   :config['codes']}

    if destn is not None:
        cc['destn'] = destn
    if allow is not None:
        cc['allow'] = allow
    if pcdef is not None:
        cc['maxQ'] = allowsim(config['instrset'], encoding, pcdef, mode=mode)
        if start is not None:
            cc['start'] = start
            
    open(output+'.json','w').write(json.dumps(cc))

def seq_write(name, instr, output, start=None, destn=None, allow=None, pcdef=None, codes=None, mode='CW'):
    seq_write_py  (instr, output, codes)
    seq_write_json(name, output, start, destn, allow, pcdef, mode=mode)

def beam_write(name, instr, output, destn, allow, mode='CW'):
    seq_write(name=name, instr=instr, output=output, destn=destn, allow=allow, mode=mode)

def ctrl_write(name, instr, output, codes=None):
    seq_write(name=name, instr=instr, output=output, codes=codes)

def allow_write(name, instr, start, pcdef, output, mode='CW'):
    seq_write(name=name, instr=instr, start=start, pcdef=pcdef, output=output, mode=mode)
