#
#  This module contains some lcls-specific code for constructing the
#  pattern path from the user-interface PVs
#

#
#  Need to monitor burst bunches,spaces PVs and set PATTERN_FOUND result.
#  Need to set heartbeat pv
#

import logging
import sys
from tools.patternprogrammer import *
from tools.pv_ca             import *
from lcls.destn              import *

def insert_space(rate):
    if 'kHz' in rate:
        rates = rate.split('k')[0]+' kHz'
    else:
        rates = rate.split('H')[0]+' Hz'
    return rates

do_cw_load  = False
do_bu_load  = False
do_apply    = False

class DestPv:
    def __init__(self, base, mode, dst):
        self.dst     = dst
        self.mode    = mode
        self.name    = lcls_destn()[dst]['name']
        pvbase = f'{base}:SC{mode:02d}:DST{dst:02d}_DES_'
        self.rate    = Pv(pvbase+'FREQUENCY')
        self.bunches = Pv(pvbase+'BUNCHES')
        self.spaces  = Pv(pvbase+'SPACES')

    def get_rate(self):
        rate = self.rate.get()
        if rate=='':
            rate='0Hz'
        return rate

    def get_bunches(self):
        bunches = int(self.bunches.get())  # float pv should be int
        return bunches

    def get_spaces(self):
        spaces = int(self.spaces.get())   # float pv should be int
        return spaces

    def cw_selected(self):
        return self.get_rate()!='0Hz'

    def cw_pattern(self,path):
        rates = insert_space(self.get_rate())
        return f'{path}/{self.name}.{rates}'

    def burst_selected(self):
        logging.debug(f'{self.name} burst_selected {self.get_bunches()}')
        return self.get_bunches()!=0 and self.get_spaces()!=0

    def burst_pattern(self,path):
        logging.debug(f'{self.name} burst_pattern [{self.get_bunches()}] [{self.get_spaces()}]')
        if self.get_bunches()==0 or self.get_spaces()==0:  # No rate pattern
            return f'{path}/{self.name}.0 Hz'
        return f'{path}/{self.name}.{self.get_bunches()}b_{self.get_spaces()}'

def main(args):
    global do_cw_load, do_bu_load, do_apply

    program = PatternProgrammer(args.pv)

    cw_path  = os.getenv('IOC_DATA')+'/sioc-sys0-ts01/TpgPatternSetup/GUNRestart'
    bu_path  = os.getenv('IOC_DATA')+'/sioc-sys0-ts01/TpgPatternSetup/GUNRestartBurst'
    chargpv = Pv(args.pv+':BUNCH_CHARGE')
    logging.debug(f'BUNCH_CHARGE {chargpv.get()}')

    laser       = DestPv(base=args.pv,mode=11,dst=0)
    dumpbsy     = DestPv(base=args.pv,mode=11,dst=2)

    cw_load_pv  = Pv(args.pv+':CONTINUOUS_LOAD' )
    bu_load_pv  = Pv(args.pv+':BURST_LOAD' )
    apply_pv    = Pv(args.pv+':APPLY')
    #  Fetch the values once so monitor isn't called back initially
    cw_load_pv.get()
    bu_load_pv.get()
    apply_pv  .get()

    #  I can't caget inside of these callbacks, defer
    def cw_load_callback(err):
        logging.debug('cw_load_callback')
        global do_cw_load
#        if cw_load_pv.get()==1:
        do_cw_load = True

    def bu_load_callback(err):
        logging.debug('bu_load_callback')
        global do_bu_load
#        if bu_load_pv.get()==1:
        do_bu_load = True

    def apply_callback(err):
        logging.debug('apply_callback')
        global do_apply
#        if apply_pv.__value__=='1':
        do_apply = True

    def cw_load():
        charge = chargpv.get()
        #  Can only be one destination for now.  Choose downstream-most.
        if dumpbsy.cw_selected():
            p = dumpbsy.cw_pattern(cw_path)
        else:
            p = laser.cw_pattern(cw_path)
        logging.debug(f'Loading path {p}')
        program.load(p,charge)

    def bu_load():
        charge = chargpv.get()
        #  Can only be one destination for now.  Choose downstream-most.
        if dumpbsy.burst_selected():
            p = dumpbsy.burst_pattern(bu_path)
        else:
            p = laser  .burst_pattern(bu_path)
        logging.debug(f'Loading path {p}')
        program.load(p,charge)

    cw_load_pv.monitor(cw_load_callback)
    bu_load_pv.monitor(bu_load_callback)
    apply_pv  .monitor(apply_callback)
#    hbeatpv = Pv(args.pv+':HEARTBEAT')

    logging.info('Ready')

    hbeat = 0
    while(True):
        for i in range(10):
            time.sleep(0.1)
            if do_cw_load:
                do_cw_load=False
                logging.info('CW Load')
                cw_load()
#                cw_load_pv.put(0)
                logging.info('CW Load complete')
            if do_bu_load:
                do_bu_load=False
                logging.info('Burst Load')
                bu_load()
#                bu_load_pv.put(0)
                logging.info('Burst Load complete')
            if do_apply:
                do_apply=False
                logging.info('Apply')
                program.apply()
#                apply_pv.put(0)
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
