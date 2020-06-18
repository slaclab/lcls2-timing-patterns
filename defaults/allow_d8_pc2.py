from seq import *

instrset = []

#  Loop here indefinitely
b0 = len(instrset)
instrset.append(FixedRateSync(marker=0,occ=1))
instrset.append(BeamRequest(0))
instrset.append(Branch.unconditional(line=b0))

title = 'Allow_D6_PC2'
    
