import collections

#  Power class defining parameters

PCDef = collections.namedtuple('PCDef',['sumQ','winQ','spacing'])

def lcls_pcdef():
    r = []
    parms = [( 0  , 455000,      0),    # Beam Off
             ( 0  , 455000,      0),    # Kicker STDBY
             ( 350, 910000, 910000),    # BC1Hz
             (3500, 910000,  91000),    # BC10Hz
             (5000, 455000,   7583),    # Diagnostic
             (6600, 182000,   7583),    # BC120Hz
             (7000, 182000,      0),    # Tuning
             (3000,   9100,      0),    # 1% MAP
	     (4500,   2730,      0),    # 5% 
	     (3000,    910,      0),    # 10%
	     (3000,    364,      0),    # 25%
             (3000,    182,      0),    # 50%
             (6000,    182,      0),    # 100%
	     (None,   None,      0),]   # Unlimited
    for p in parms:
        r.append(PCDef._make(p))
    return r

nallow = 14
