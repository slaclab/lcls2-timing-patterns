import collections

#  Power class defining parameters

PCDef = collections.namedtuple('PCDef',['sumQ','winQ','spacing'])

def lcls_pcdef():
    r = []
    parms = [( 0  , 455000,      0),
             ( 0  , 455000,      0),
             ( 330, 910000, 910000),
             (None,   None,  91000),
             (5000, 455000,      0),
             (6600, 182000,   9100),
             (7000, 182000,      0),
             (3000,   9100,      0),
             (3000,    182,      0),
             (6000,    182,      0),]
    for p in parms:
        r.append(PCDef._make(p))
    return r

nallow = 14
