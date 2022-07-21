from tools.seq import *

instrset = []
instrset.append( ControlRequest(3) )
instrset.append( FixedRateSync(marker=6, occ=512 ) )
instrset.append( ControlRequest(1) )
instrset.append( FixedRateSync(marker=6, occ=512 ) )
instrset.append( Branch.unconditional(0) )
