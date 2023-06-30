#  Make a pattern that includes the hutch sequence as a demonstration
#  of RIX triggering needs
import logging
import argparse
from tools.trigger import add_triggers

def main():
    global args
    parser = argparse.ArgumentParser(description='train pattern generator')
    parser.add_argument("--path", required=True , help="file output path")
    parser.add_argument("--simulate", default=1., type=float, help="simulation time (seconds)")
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--debug"  , action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    #  Define the triggers
    p = {'0':{'name':'Andor'    , 'marker':{'type':'ctrl' , 'index':280}, 'destn':{'type':'DC'}},
         '1':{'name':'Opal'     , 'marker':{'type':'ctrl' , 'index':281}, 'destn':{'type':'DC'}},
         '2':{'name':'OpalBeam' , 'marker':{'type':'ctrl' , 'index':281}, 'destn':{'type':'INCL','mask':[4]}},}

    add_triggers(args.path,p,start=0,stop=int(910000*args.simulate))
    
if __name__=='__main__':
    main()
