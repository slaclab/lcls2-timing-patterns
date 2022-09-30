from tools.seq import *

instrset = []
instrset.append( ControlRequest(1) )
iinstr = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=2048) )
instrset.append( Branch.conditional(line=iinstr, counter=3, value=6) )
instrset.append( FixedRateSync(marker=6, occ=1024 ) )
instrset.append( Branch.unconditional(0) )
