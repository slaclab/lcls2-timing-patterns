#This program is supposed to define the right path to Load the timing pattern to TPG
from epics import caget, caput, camonitor, PV
from tools.patternprogrammer import PatternProgrammer
from tools.seqprogram import *
import json
import os
import time
import logging

class Apply2Tpg(object):
        def __init__(self):
          self.pv='TPG:SYS0:1' #main PV name for TPG in PROD
          self.programmer = PatternProgrammer(self.pv)
          self.charge = PV(self.pv+':BUNCH_CHARGE')
          
  
        def apply(self):
          app_macro ='APP'
          rootpath = os.getenv(app_macro)
          self.path =rootpath+'/TpgPatternSetup/lcls2-timing-patterns/GUNRestart/'
          laserRate = PV('TPG:SYS0:1:SC11:DST00_DES_FREQUENCY')
          dumpBsyRate = PV('TPG:SYS0:1:SC11:DST02_DES_FREQUENCY')
          self.programmer.apply()

def main():
        activate= Apply2Tpg()
        activate.apply() 

if __name__ == '__main__':
 #   parser = argparse.ArgumentParser(description='pattern pva programming')
 #   parser.add_argument("--pattern", required=True, help="pattern subdirectory")
 #   parser.add_argument("--charge" , required=True, help="bunch charge, pC", type=int)
 #   parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
 #   args = parser.parse_args()

 #   cProfile.run('main(args)')
    logging.basicConfig(level=logging.DEBUG)
    main()





