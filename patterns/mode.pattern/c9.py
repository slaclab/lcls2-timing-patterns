from tools.seq import *

instrset = []
instrset.append( ControlRequest(1) )
instrset.append( FixedRateSync(marker=6, occ=1080 ) )
instrset.append( Branch.unconditional(0) )
