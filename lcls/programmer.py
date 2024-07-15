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
sys.path.append("..")
from epics import PV
import os
import time
import argparse
from tools.patternprogrammer import PatternProgrammer
from tools.pv_ca import Pv
from datetime import datetime

#    Capture a PV update in a local variable
class MonitoredPv:
    def __init__(self, name):
        self._updated = False
        def callback(err,self=self):
            self._updated=True
        self.pv = Pv(name,callback)

    def updated(self):
        if self._updated:
            self._updated = False
            return True
        return False

class LogPv:
    def __init__(self, name):
        self.pv = PV(name)
        self.msg = []

    def append(self, msg):
        if len(self.msg) > 6:
            self.msg = self.msg[1:]
        self.msg.append(msg)
        s = '\n'.join(self.msg)
        self.pv.put(s)

#
#  Process the pattern selection for a given SC mode.
#  Exit upon mode change, so all the PV references can change.
#
def run_mode(program,mode_pv):
    mode_pv.updated()
    mode = mode_pv.pv.get()
    logging.info(f'mode: {mode}')
    patt_path  = os.getenv('IOC_DATA')+f'/{args.tpg_ioc}/TpgPatternSetup/patterns'
    print(patt_path)

    log_pv   = LogPv(args.pv+':LOG')
    log_pv.append(f'Mode {mode}')
    
    load_pv = MonitoredPv(args.pv+':PATT_LOAD' )
    apply_pv    = MonitoredPv(args.pv+':APPLY')

    #Debug prints
    log_pv.append(f'Monitoring started...')
    
    chargpv   = Pv(args.pv+':BUNCH_CHARGE')
    pattPV = PV(args.pv+':PATT_PATH')
        
    def man_load():
        charge = chargpv.get()
        p = patt_path+'/'+pattPV.get(as_string=True)
        logging.info(f'Loading path {p}')
        program.load(p,charge)
        base = p.split('/')[-2] + "/" + p.split('/')[-1] + f" | {datetime.now()}"
        print(f'base: {base}')
        log_pv.append(f'Loaded {base}')
        
    hbeatpv = Pv(args.pv+':PATT_PROG_HRTBT')

    logging.info(f'Mode {mode} Ready')

    load_pv.updated()
    apply_pv  .updated()

    hbeat = 0
    while(True):
        for i in range(10):
            time.sleep(0.1)
            if load_pv.updated():
                logging.info('Pattern Load')
                man_load()
                logging.info('Pattern Load complete')
            if apply_pv.updated():
                logging.info('Apply')
                program.apply()
                logging.info('Apply complete')

        hbeat += 1
        logging.debug(f'hbeat {hbeat}')
        hbeatpv.put(hbeat)

        if mode_pv.updated():
            logging.debug(f'---mode changed---')
            break
            
def main(args):
    global do_cw_load, do_bu_load, do_apply

    program = PatternProgrammer(args.pv)

    mode_ctl = MonitoredPv(args.pv+':MODE')
    while True:
        run_mode(program,mode_ctl)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pattern pva programming')
    parser.add_argument("--pv",  default='TPG:SYS0:1', help="TPG base pv; e.g. ")
    parser.add_argument("--tpg-ioc", default='sioc-sys0-ts01', help="Tpg ioc; e.g. ")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    main(args)