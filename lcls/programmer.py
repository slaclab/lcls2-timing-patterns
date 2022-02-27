#
#  This module contains some lcls-specific code for constructing the
#  pattern path from the user-interface PVs
#

import logging
import sys
from tools.patternprogrammer import *
from tools.pv_ca             import *

def pattern_name(dindex,dest,rate):
    rate = rate.strip('Hz')
    if rate.isdigit(): rate+= " Hz"
    if 'k' in rate:
        rate = rate.strip('k')
        rate+=" kHz"
    return dindex+' SC1 '+dest+'.'+rate

doload  = False
doapply = False

def main(args):
    global doload
    global doapply

    program = PatternProgrammer(args.pv)

    path    = os.getenv('IOC_DATA')+'/sioc-sys0-ts01/TpgPatternSetup/GUNRestart/'
    chargpv = Pv(args.pv+':BUNCH_CHARGE')
    logging.debug(f'BUNCH_CHARGE {chargpv.get()}')

    laserRate   = Pv(args.pv+':SC11:DST00_DES_FREQUENCY')
    dumpBsyRate = Pv(args.pv+':SC11:DST02_DES_FREQUENCY')

    loadpv  = Pv(args.pv+':CONTINUOUS_LOAD' )
    applypv = Pv(args.pv+':CONTINUOUS_APPLY')
    #  Fetch the values once so monitor isn't called back initially
    loadpv.get()
    applypv.get()

    #  I can't caget inside of these callbacks, defer
    def load_callback(err):
        logging.debug('load_callback')
        global doload
        doload = True

    def load():
        charge = chargpv.get()
        #  Can only be one destination for now.  Choose downstream-most.
        _dumpBsyRate = dumpBsyRate.get()
        if _dumpBsyRate!='0Hz':
            p = path + pattern_name('2','DUMPBSY',_dumpBsyRate)
        else:
            p = path + pattern_name('0','Laser',laserRate.get())
        logging.debug(f'Loading path {p}')
        program.load(p,charge)

    def apply_callback(err):
        logging.debug('apply_callback')
        global doapply
        doapply = True

    loadpv .monitor(load_callback)
    applypv.monitor(apply_callback)
#    hbeatpv = Pv(args.pv+':HEARTBEAT')

    hbeat = 0
    while(True):
        for i in range(10):
            time.sleep(0.1)
            if doload:
                doload=False
                logging.info('Load')
                load()
                logging.info('Load complete')
            if doapply:
                doapply=False
                logging.info('Apply')
                program.apply()
                logging.info('Apply complete')
        hbeat += 1
        logging.debug(f'hbeat {hbeat}')
#        hbeatpv.put(alive)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pv",  default='TPG:SYS0:1', help="TPG base pv; e.g. ")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    cProfile.run('main(args)')
    main(args)
