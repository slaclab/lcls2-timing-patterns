from seq import *

instrset = []

instrset.append(FixedRateSync(marker=6,occ=1))
instrset.append(BeamRequest(0))

#  Loop here indefinitely
b0 = len(instrset)
instrset.append(Branch.unconditional(line=b0))
   
