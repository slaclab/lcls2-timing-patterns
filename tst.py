from seq import *

instrset = []
instrset.append(FixedRateSync(marker=6,occ=1))
# loop A: 140 trains
startreq = len(instrset)
#   4 bunches / train
instrset.append(BeamRequest(0))
iinstr=len(instrset)
instrset.append( FixedRateSync(marker=0, occ=10 ) )
instrset.append(BeamRequest(0))
instrset.append(Branch.conditional(line=iinstr,counter=1,value=2))
instrset.append( FixedRateSync(marker=0, occ=70 ) )
instrset.append( Branch.conditional(startreq, 0, 139) )
# end loop A
# loop B: 8960 trains
startreq = len(instrset)
#   4 bunches / train
instrset.append(BeamRequest(0))
iinstr=len(instrset)
instrset.append( FixedRateSync(marker=0, occ=10 ) )
instrset.append(BeamRequest(0))
instrset.append(Branch.conditional(line=iinstr,counter=2,value=2))
instrset.append( FixedRateSync(marker=0, occ=70 ) )
instrset.append( Branch.conditional(startreq, 0, 255) )
instrset.append( Branch.conditional(startreq, 1, 34) )
# end loop B
startreq = len(instrset)
instrset.append( Branch.unconditional(startreq) )
