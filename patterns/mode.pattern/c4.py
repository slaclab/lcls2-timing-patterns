from tools.seq import *

instrset = []
instrset.append( ControlRequest(7) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(3) )
# loop: req 1 of step 7 and repeat 5
start = len(instrset)
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( ControlRequest(1) )
instrset.append( Branch.conditional(start, 0, 5) )
instrset.append( FixedRateSync(marker=6, occ=7 ) )
instrset.append( Branch.unconditional(0) )
