from tools.seq import *

instrset = []
instrset.append( ControlRequest(1) )
iinstr = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=2048) )
instrset.append( Branch.conditional(line=iinstr, counter=3, value=3) )
instrset.append( FixedRateSync(marker=6, occ=1528 ) )
instrset.append( Branch.unconditional(0) )
