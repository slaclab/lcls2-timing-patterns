from tools.seq import *

instrset = []
instrset.append( ControlRequest(1) )
instrset.append( FixedRateSync(marker=6, occ=32 ) )
instrset.append( Branch.unconditional(0) )
