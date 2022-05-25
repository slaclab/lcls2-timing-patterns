import collections

#  Power class defining parameters

PCDef = collections.namedtuple('PCDef',['sumQ','winQ','spacing'])

def lcls_pcdef():
    r = []
    parms = [( 0  , 455000,      0),
             ( 0  , 455000,      0),
             ( 350, 910000, 910000),
             (3500, 910000,  91000),
             (5000, 455000,      0),
             (6600, 182000,   7583),
             (7000, 182000,      0),
             (3000,   9100,      0),
	     (4500,   2730,      0),             
	     (3000,    910,      0),
	     (3000,    364,      0),
             (3000,    182,      0),
             (6000,    182,      0),
	     (None,   None,      0),]
    for p in parms:
        r.append(PCDef._make(p))
    return r

nallow = 14
