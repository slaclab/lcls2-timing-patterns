from tools.seq import *

instrset = []
instrset.append( BeamRequest(0) )
instrset.append( FixedRateSync(5,1) )
instrset.append( Branch.unconditional(0) )
