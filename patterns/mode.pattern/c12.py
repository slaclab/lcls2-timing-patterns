from tools.seq import *

instrset = []
instrset.append( ControlRequest(1) )
iinstr = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=2048) )
instrset.append( Branch.conditional(line=iinstr, counter=3, value=13) )
instrset.append( FixedRateSync(marker=6, occ=488 ) )
instrset.append( Branch.unconditional(0) )
