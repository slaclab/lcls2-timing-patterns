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
import glob
from tools.patternprogrammer import *
from tools.pv_ca             import *
from lcls.destn              import *

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
              '1000Hz':'1 kHz',
              '1400Hz':'1.4 Hz',
              '5000Hz':'5 kHz',
              '10kHz' :'10 Hz',
              '23kHz' :'23 Hz',
              '33kHz' :'33 Hz',
              '46kHz' :'46 Hz',
              '93kHz' :'93 Hz',
              '464kHz':'464 Hz',
              '929kHz':'929 Hz',}

#    Choose downstream most destination with rate
def get_cw_dst(dst_list):
    dst = dst_list[0]
    for i in dst_list:
        if i.cw_selected():
            dst = i
    return dst

#    Choose downstream most destination with bunches
def get_bu_dst(dst_list):
    dst = dst_list[0]
    for i in dst_list:
        if i.burst_selected():
            dst = i
    return dst

#    Capture a PV update in a local variable
class MonitoredPv:
    def __init__(self, name):
        self._updated = False
#        self.pv = Pv(name)
#        self.pv.get()
        def callback(err,self=self):
            self._updated=True
#        self.pv.monitor(callback)
        self.pv = Pv(name,callback)

    def updated(self):
        if self._updated:
            self._updated = False
            return True
        return False

class DestPv:
    def __init__(self, base, mode, dst, path):
        self.dst     = dst
        self.name    = lcls_destn()[dst]['name']

        pvbase = f'{base}:{mode}:DST{dst:02d}_DES_'
        self.rate    = Pv(pvbase+'FREQUENCY')
        self.bunches = Pv(pvbase+'BUNCHES')
        self.spaces  = Pv(pvbase+'SPACES')

        name = path+'/'+self.name+'.'
        self.patterns = [p[len(name):] for p in glob.iglob(f'{name}*')]
        logging.debug(f'patterns {name} {self.patterns}')

        def callback(err,self=self):
            self.callback(err)

        self.rate   .get()
        self.bunches.get()
        self.bunches.monitor(callback)

        self.spaces.get()
        self.spaces.monitor(callback)

        self.pattern_found = False

        self.callback(None)

    def callback(self,err):
        name = self.burst_pattern(path='').split('.')[1]
        self.pattern_found = name in self.patterns
        logging.debug(f'{self.pattern_found} : {name}')

    def get_rate(self):
        rate = self.rate.get()
        logging.debug(f'get_rate {self.dst} {rate}')
        if rate=='' or rate=='0':
            rate='0Hz'
        return rate

    def get_bunches(self):
        if self.bunches.__value__ is not None:
            return int(self.bunches.__value__)
        logging.warning(f'{self.bunches.pvname} not connected')
        return 0  # not connected

    def get_spaces(self):
        if self.spaces.__value__ is not None:
            return int(self.spaces.__value__)
        logging.warning(f'{self.spaces.pvname} not connected')
        return 1

    def cw_selected(self):
        return self.get_rate()!='0Hz'

    def cw_pattern(self,path):
        rates = rate_names[self.get_rate()]
        return f'{path}/{self.name}.{rates}'

    def burst_selected(self):
#        logging.debug(f'{self.name} burst_selected {self.get_bunches()}')
        return self.get_bunches()!=0 and self.get_spaces()!=0

    def burst_pattern(self,path):
        logging.debug(f'{self.name} burst_pattern [{self.get_bunches()}] [{self.get_spaces()}]')
        if self.get_bunches()<2:
            result = f'{path}/{self.name}.{self.get_bunches()}b'
        else:
            result = f'{path}/{self.name}.{self.get_bunches()}b_{self.get_spaces()}'
        return result

class PatternFound:
    def __init__(self, base, dst):
        self.value   = Pv(base+':BURST_PATTERN_FOUND')
        self.desc    = Pv(base+':BURST_PATTERN_FOUND.DESC')
        self.dst     = dst
        self.found   = False
        self.value.put(0)

    def process(self):
        found = False
        if get_bu_dst(self.dst).pattern_found:
            found = True
        if found != self.found:
            logging.debug(f'PatternFound: {found}')
            self.found = found
            self.value.put(1 if found else 0)

#
#  Process the pattern selection for a given SC mode.
#  Exit upon mode change, so all the PV references can change.
#
def run_mode(program,mode_pv):
    mode_pv.updated()
    mode = mode_pv.pv.get()
    logging.info(f'mode: {mode}')
    cw_path  = os.getenv('IOC_DATA')+'/sioc-sys0-ts01/TpgPatternSetup/GUNRestart'
    bu_path  = os.getenv('IOC_DATA')+'/sioc-sys0-ts01/TpgPatternSetup/GUNRestartBurst'

    cw_load_pv  = MonitoredPv(args.pv+':CONTINUOUS_LOAD' )
    bu_load_pv  = MonitoredPv(args.pv+':BURST_LOAD' )
    apply_pv    = MonitoredPv(args.pv+':APPLY')

    chargpv = Pv(args.pv+':BUNCH_CHARGE')

    dst         = [DestPv(base=args.pv,mode=mode,dst=i,path=bu_path) for i in range(6)]
    found       = PatternFound(base=args.pv,dst=dst)

    def cw_load():
        charge = chargpv.get()
        p = get_cw_dst(dst).cw_pattern(cw_path)
        logging.info(f'Loading path {p}')
        program.load(p,charge)

    def bu_load():
        charge = chargpv.get()
        p = get_bu_dst(dst).burst_pattern(bu_path)
        logging.info(f'Loading path {p}')
        program.load(p,charge)

#    hbeatpv = Pv(args.pv+':HEARTBEAT')

    logging.info(f'Mode {mode} Ready')

    #  Clear the updated flags
    cw_load_pv.updated()
    bu_load_pv.updated()
    apply_pv  .updated()

    hbeat = 0
    while(True):
        for i in range(10):
            time.sleep(0.1)
            if cw_load_pv.updated():
                logging.info('CW Load')
                cw_load()
                logging.info('CW Load complete')
            if bu_load_pv.updated():
                logging.info('Burst Load')
                bu_load()
                logging.info('Burst Load complete')
            if apply_pv.updated():
                logging.info('Apply')
                program.apply()
                logging.info('Apply complete')

        found.process()

        hbeat += 1
#        logging.debug(f'hbeat {hbeat}')
#        hbeatpv.put(alive)

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
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    cProfile.run('main(args)')
    main(args)
