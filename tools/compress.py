import argparse
import json

#  Compress by identifying runs or repeats
def list_compress(a):
    d_seq = []
    d_rep = []
    #  Use a dictionary to pass-by-ref
    d = {'vfirst':None, 'vlast':None, 'vrep':None, 'nrep':1}

    def _seq_append(v,d=d):
        d_seq.append((d['vfirst'],d['vlast']) if d['vlast']>d['vfirst'] else (d['vfirst'],))
        d['vfirst'] = v
        d['vlast']  = v+1

    def _rep_append(v,d=d):
        d_rep.append((d['vrep'],d['nrep']))
        d['vrep'] = v
        d['nrep'] = 1

    for v in a:
        if d['vlast'] is None:
            d['vfirst'] = v
            d['vlast' ] = v+1
            d['vrep'  ] = v
        elif v==d['vrep']:
            d['nrep'] += 1
            _seq_append(v)
        elif v==d['vlast']:
            d['vlast'] = v+1
            _rep_append(v)
        else:
            _rep_append(v)
            _seq_append(v)

    if d['vfirst'] is not None:
        d_seq.append((d['vfirst'],d['vlast']) if d['vlast']>d['vfirst'] else (d['vfirst'],))
        d_rep.append((d['vrep'],d['nrep']))

    #  Make some judgement when it's worth saving compressed list
    if (len(d_rep) < len(a)//2) and (len(d_rep) < len(d_seq)):
        return {'compress_rep':d_rep}
    if (len(d_seq) < len(a)//2):
        return {'compress_seq':d_seq}
    return a

def list_seq_decompress(a):
    d = []
    for e in a:
        d.extend([i for i in range(e[0],e[-1])])
    return d

def list_rep_decompress(a):
    d = []
    for e in a:
        d.extend([e[0]]*e[-1])
    return d

def compress(a):
    if isinstance(a,list) and len(a):
        v = a[0]
        if isinstance(v,int):
            return list_compress(a)
        if isinstance(v,dict) or isinstance(v,list):
            l = []
            for e in a:
                l.append(compress(e))
            return l
        return a
    elif isinstance(a,dict):
        d = {}
        for k,v in a.items():
            d[k] = compress(v)
        return d
    return a

def decompress(a):
    if isinstance(a,list) and len(a):
        v = a[0]
        if isinstance(v,dict) or isinstance(v,list):
            l = []
            for e in a:
                l.append(decompress(e))
            return l
        return a
    if isinstance(a,dict):
        if 'compress_seq' in a:
            return list_seq_decompress(a['compress_seq'])
        elif 'compress_rep' in a:
            return list_rep_decompress(a['compress_rep'])
        else:
            d = {}
            for k,v in a.items():
                d[k] = decompress(v)
            return d
    return a

if __name__=='__main__':

    parser = argparse.ArgumentParser(description='compression')
    parser.add_argument("--path", help="path to pattern directories", type=str, default=None)
    args = parser.parse_args()
    
    def _test(a):
        print('==input {}'.format(a))
        c = compress(a)
        print('  compr {}'.format(c))
        d = decompress(c)
        print('  dcmpr {}'.format(d))
        if a!=d:
            raise RuntimeError('Failed: {} {}'.format(a,d))

    def _test_seq(d):
        _test(d)
        _test({'stuff':d})
        _test([d,])
        _test((d,))

    _test_seq({'list':[0,1,2,3,4,6,8,9,10,11,12,13]})
    _test_seq({'list':[0,2,2,2,2,9,13,13,13,13]})

    if args.path:
        _test(json.load(open(args.path,'r')))

    print('passed')
