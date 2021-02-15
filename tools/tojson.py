from tools.seq import *
import glob
import argparse

#  Convert .py to .json file for faster loading
def tojson(fname):
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
    ofile = fname.replace('.py','.json')
    open(ofile,mode='w').write(json.dumps(config))

def main():
    parser = argparse.ArgumentParser(description='convert .py to .json')
    parser.add_argument("-d", "--dir" , required=True , help="directory")
    args = parser.parse_args()

    for p in glob.iglob(args.dir+'/*.py'):
        print('Converting {}'.format(p))
        tojson(p)

if __name__=='__main__':
    main()
