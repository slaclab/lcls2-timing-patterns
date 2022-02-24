#This program is supposed to define the right path to Load the timing pattern to TPG
from epics import caget, caput, camonitor, PV
from tools.patternprogrammer import PatternProgrammer
from tools.seqprogram import *
import json
import os
import time
import logging

class Push2Tpg(object):
        def __init__(self):
          self.pv='TPG:SYS0:1' #main PV name for TPG in PROD
          self.programmer = PatternProgrammer(self.pv)
          self.charge = PV(self.pv+':BUNCH_CHARGE')
          
        def dest_rate(self,dindex,dest,ratepv):
          rate = ratepv.get()
          rate = rate.strip('Hz')
          if rate.isdigit(): rate+= " Hz"
          if 'k' in rate:
            rate = rate.strip('k')
            rate+=" kHz"
          self.path+= dindex+' SC1 '+dest+'.'+rate
          print('actual final path****** '+self.path)
  
        def path(self):
          app_macro ='APP'
          rootpath = os.getenv(app_macro)
          self.path =rootpath+'/TpgPatternSetup/lcls2-timing-patterns/GUNRestart/'
          laserRate = PV('TPG:SYS0:1:SC11:DST00_DES_FREQUENCY')
          dumpBsyRate = PV('TPG:SYS0:1:SC11:DST02_DES_FREQUENCY')
          if(laserRate.get()!='0Hz'): 
               print('Laser NOT 0Hz'+laserRate.get())
               if(dumpBsyRate.get()!='0Hz'):
                 if(laserRate.timestamp>dumpBsyRate.timestamp):
                   print("I pick Laser")
                   self.dest_rate('0','Laser',laserRate)
                   charge = self.charge.get()
                   self.programmer.load(self.path,charge)
                 else: 
                   print("I pick DumpBSY")
                   self.dest_rate('2','DUMPBSY',dumpBsyRate)
                   charge = self.charge.get()
                   self.programmer.load(self.path,charge)
               else: 
                 self.dest_rate('0','Laser',laserRate)
                 charge = self.charge.get()
                 self.programmer.load(self.path,charge)
          else:
            if(dumpbsyRate.get()!='0Hz'):
              self.dest_rate('2','DUMPBSY',dumpBsyRate)
              charge = self.charge.get()
              self.programmer.load(self.path,charge)

def main():
        push= Push2Tpg()
        push.path() 

if __name__ == '__main__':
 #   parser = argparse.ArgumentParser(description='pattern pva programming')
 #   parser.add_argument("--pattern", required=True, help="pattern subdirectory")
 #   parser.add_argument("--charge" , required=True, help="bunch charge, pC", type=int)
 #   parser.add_argument("--pv"     , default='TPG:SYS2:2', help="TPG base pv; e.g. ")
 #   args = parser.parse_args()

 #   cProfile.run('main(args)')
    logging.basicConfig(level=logging.DEBUG)
    main()





