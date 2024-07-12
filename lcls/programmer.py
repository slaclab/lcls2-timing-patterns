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

#
#  Some policies
#
#    Just make a whole dictionary to translate rate button names to pattern names
rate_names = {'0Hz'   :'0 Hz', 
              '1Hz'   :'1 Hz',
              '10Hz'  :'10 Hz',
              '50Hz'  :'50 Hz',
              '100Hz' :'100 Hz',
              '200Hz' :'200 Hz',
              '500Hz' :'500 Hz',
              '1kHz':'1 kHz',
              '1.4kHz':'1.4 kHz',
              '5kHz':'5 kHz',
              '10kHz' :'10 kHz',
              '23kHz' :'23 kHz',
              '33kHz' :'33 kHz',
              '46kHz' :'46 kHz',
              '93kHz' :'93 kHz',
              '464kHz':'464 kHz',
              '929kHz':'929 kHz',}
ac_rate_names = {'0Hz'   :'0 Hz', 
              '1Hz'   :'1 Hz',
              '10Hz'  :'10 Hz',
              '30Hz'  :'30 Hz',
              '60Hz' :'60 Hz',
              '90Hz' :'90 Hz',
              '110Hz' :'110 Hz',
              '119Hz':'119 Hz',
              '120Hz':'120 Hz',}

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

# TODO: change the functionality of this so the pv always has a non NULL value
class LogPv:
    def __init__(self, name):
        self.pv = Pv(name)
        self.msg = []

    def append(self, msg):
        if len(self.msg) > 2:
            self.msg = self.msg[1:]
        self.msg.append(msg)
        while True:
            s = '\n'.join(self.msg)
            if len(s) < 40:
                break
            self.msg = self.msg[1:]
        self.pv.put(s)

#
#  Process the pattern selection for a given SC mode.
#  Exit upon mode change, so all the PV references can change.
#
def run_mode(program,mode_pv):
    mode_pv.updated()
    mode = mode_pv.pv.get()
    logging.info(f'mode: {mode}')
    mn_path  = os.getenv('IOC_DATA')+f'/{args.tpg_ioc}/TpgPatternSetup/patterns'
    print(mn_path)

    log_pv   = LogPv(args.pv+':LOG')
    log_pv.append(f'Mode {mode}')
    
    man_load_pv = MonitoredPv(args.pv+':MANUAL_LOAD' )
    apply_pv    = MonitoredPv(args.pv+':APPLY')

    #Debug prints
    log_pv.append(f'Monitoring started...')

    chargpv   = Pv(args.pv+':BUNCH_CHARGE')
    manpattPV = PV(args.pv+':MANUAL_PATH')
        
    def man_load():
        charge = chargpv.get()
        p = mn_path+'/'+manpattPV.get(as_string=True)
        logging.info(f'Loading path {p}')
        program.load(p,charge)
        base = p.split('/')[-1]
        log_pv.append(f'Loaded {base}')
        
    hbeatpv = Pv(args.pv+':PATT_PROG_HRTBT')

    logging.info(f'Mode {mode} Ready')

    man_load_pv.updated()
    apply_pv  .updated()

    hbeat = 0
    while(True):
        for i in range(10):
            time.sleep(0.1)
            if man_load_pv.updated():
                logging.info('Manual Load')
                man_load()
                logging.info('Manual Load complete')
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

    #cProfile.run('main(args)')
    main(args)
