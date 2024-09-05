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
from epics import PV, caput
import os
import time
import argparse
from tools.patternprogrammer import PatternProgrammer
from tools.pv_ca import Pv
from datetime import datetime
import ScPatternSelect

TS_PAIRS = {"TS1" : "TS4", "TS2": "TS5", "TS3": "TS6"}

#    Capture a PV update in a local variable
class MonitoredPv:
    def __init__(self, name):
        self._updated = False

        def callback(err, self=self):
            self._updated = True

        self.pv = Pv(name, callback)

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
        s = "\n".join(self.msg)
        self.pv.put(s)


#
#  Process the pattern selection for a given SC mode.
#  Exit upon mode change, so all the PV references can change.
#
def run_mode(program, mode_pv):
    mode_pv.updated()
    mode = mode_pv.pv.get()
    logging.info(f"mode: {mode}")
    patt_path = os.getenv("IOC_DATA") + f"/{args.tpg_ioc}/TpgPatternSetup/patterns"
    logging.info(f"Path to patterns: {patt_path}")

    log_pv = LogPv(args.pv + ":LOG")
    log_pv.append(f"Mode {mode}")

    # load_pv = MonitoredPv(args.pv+':PATT_LOAD' )
    load_pv = MonitoredPv(args.pv + ":MANUAL_LOAD")
    apply_pv = MonitoredPv(args.pv + ":APPLY")

    # Debug prints
    log_pv.append(f"Monitoring started...")

    chargpv = Pv(args.pv + ":BUNCH_CHARGE")
    pattPV = PV(args.pv + ":MANUAL_PATH")

    patt_sel = ScPatternSelect.ScPatternSelect("SYS0", "1", "sioc-sys0-ts01")

    loadedPV = PV(patt_sel.globals.get_pattern_loaded_pv())
    appliedPV = PV(patt_sel.globals.get_pattern_running_pv())

    def man_load():
        charge = chargpv.get()
        pattern_to_load = pattPV.get(as_string=True)
        p = patt_path + "/" + pattern_to_load
        logging.info(f"Loading path {p}")
        program.load(p, charge)
        base = p.split("/")[-2] + "/" + p.split("/")[-1] + f" | {datetime.now()}"
        log_pv.append(f"Loaded {base}")
        loadedPV.put(pattern_to_load)
        if not patt_sel.get_is_patt_table_available():
            logging.info("man_load not able to use nttable")
        if patt_sel.get_is_patt_table_available():
            logging.info("man_load can us the nttable")
        return pattern_to_load

    def write_to_data_pvs(loaded_pattern):
        """
        Write to the meta data pvs that hold the meta data for the currently running pattern
        """
        appliedPV.put(loaded_pattern)
        patt_data = patt_sel.get_pattern_data(loaded_pattern)
        print(f"pattern table available: {patt_sel.get_is_patt_table_available()}")

        for dest in patt_sel.globals.DEST_NAMES:
            # write to time source
            write_to_time_source(dest, patt_data)
            
            # write to offset
            dest_offset = patt_data[f"{dest}{patt_sel.globals.OFFSET_SFX}"]
            dest_rate = patt_data[f"{dest}{patt_sel.globals.RATE_SFX}"]
            write_to_offset(dest, dest_offset)

            # write to timeslot
            write_to_ts(dest, dest_offset, dest_rate)

    def write_to_time_source(dest, patt_data):
        """
        determins the timing source and writes to the timeing source pv
        """
        dest_time_source = patt_data[f"{dest}{patt_sel.globals.TSOURCE_SFX}"]
        if dest_time_source.__contains__("FR"):
            dest_time_source = 0
        elif dest_time_source.__contains__("AC"):
            dest_time_source = 1
        elif dest_time_source.__contains__("B"):
            dest_time_source = 2
        else:
            dest_time_source = 0
        caput(patt_sel.globals.get_timeing_source_pv(dest), dest_time_source)

    def write_to_offset(dest, dest_offset):
        """
        Writes to the offset if the dest is fixed rate
        """
        if dest_offset.__contains__("off"):
            dest_offset = dest_offset.split(" ")
            dest_offset = int(dest_offset[1])
        else:
            dest_offset = 0
        caput(patt_sel.globals.get_offset_pv(dest), dest_offset)

    def write_to_ts(dest, dest_offset, dest_rate):
        """
        Writes to the time slot if the dest is AC
        """
        if not dest_offset.__contains__("TS"):
            caput(patt_sel.globals.get_dest_timeslot_pv(dest), "None")
            caput(patt_sel.globals.get_dest_timeslot_mask_pv(dest), 0)
            return
        timeslot_data = determin_ts(dest_offset, dest_rate)
        caput(patt_sel.globals.get_dest_timeslot_pv(dest), timeslot_data[0])
        caput(patt_sel.globals.get_dest_timeslot_mask_pv(dest), timeslot_data[1])

    def determin_ts(dest_timslot, dest_rate):
        """
        returns a tuple of the timeslot string and the timeslotmask
        i.e.
        ["TS1, TS4", 9]
        """
        ts_mask = 0
        first_itteration = True

        timeslots = []
        timeslots.append(dest_timslot)

        if dest_rate > 60:
            timeslots.append(TS_PAIRS[dest_timslot])

        for timeslot in timeslots:
            if first_itteration:
                ts_message = timeslot
                first_itteration = False
            else:
                ts_message = f"{ts_message}, {timeslot}"

            ts_num = int(timeslot.replace("TS", ""))
            ts_mask = ts_mask + (1<<(ts_num-1))

        timeslot_data = [ts_message, ts_mask]

        return timeslot_data


    hbeatpv = Pv(args.pv + ":PATT_PROG_HRTBT")

    logging.info(f"Mode {mode} Ready")

    load_pv.updated()
    apply_pv.updated()

    hbeat = 0
    while True:
        # if not is_patt_sel_available:
        # is_patt_sel_available = connect_to_pattern_table()
        # print("checking for pattern table")
        for i in range(10):
            time.sleep(0.1)
            if load_pv.updated():
                logging.info("Pattern Load")
                loaded_pattern = man_load()
                logging.info("Pattern Load complete")
            if apply_pv.updated():
                logging.info("Apply")
                write_to_data_pvs(loaded_pattern)
                program.apply()
                logging.info("Apply complete")

        hbeat += 1
        logging.debug(f"hbeat {hbeat}")
        hbeatpv.put(hbeat)

        if mode_pv.updated():
            logging.debug(f"---mode changed---")
            break


def main(args):
    global do_cw_load, do_bu_load, do_apply

    program = PatternProgrammer(args.pv)

    mode_ctl = MonitoredPv(args.pv + ":MODE")
    while True:
        run_mode(program, mode_ctl)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pattern pva programming")
    parser.add_argument("--pv", default="TPG:SYS0:1", help="TPG base pv; e.g. ")
    parser.add_argument("--tpg-ioc", default="sioc-sys0-ts01", help="Tpg ioc; e.g. ")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    main(args)
