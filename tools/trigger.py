from tools.seq import FixedRateSync,ACRateSync
from tools.globals import *
import numpy as np
import json

def add_triggers(path,q=None,start=0,stop=TPGSEC):

    #  Define the triggers
    p = {'0' :{'name':'Diag01H'  , 'marker':{'type':'ctrl', 'index': 64}, 'destn':{'type':'INCL','mask':[1]}},
         '1' :{'name':'Diag010H' , 'marker':{'type':'ctrl', 'index': 65}, 'destn':{'type':'INCL','mask':[1]}},
         '2' :{'name':'Diag0100H', 'marker':{'type':'ctrl', 'index': 66}, 'destn':{'type':'INCL','mask':[1]}},
         '3' :{'name':'Linac1H'  , 'marker':{'type':'ctrl', 'index': 80}, 'destn':{'type':'INCL','mask':[2,3,4,15]}},
         '4' :{'name':'Linac10H' , 'marker':{'type':'ctrl', 'index': 81}, 'destn':{'type':'INCL','mask':[2,3,4,15]}},
         '5':{'name':'Linac100H' , 'marker':{'type':'ctrl', 'index': 82}, 'destn':{'type':'INCL','mask':[2,3,4,15]}},
         '6':{'name':'UndH1H'    , 'marker':{'type':'ctrl', 'index': 96}, 'destn':{'type':'INCL','mask':[3]}},
         '7':{'name':'UndH10H'   , 'marker':{'type':'ctrl', 'index': 97}, 'destn':{'type':'INCL','mask':[3]}},
         '8':{'name':'UndH100H'  , 'marker':{'type':'ctrl', 'index': 98}, 'destn':{'type':'INCL','mask':[3]}},
         '9':{'name':'UndS1H'    , 'marker':{'type':'ctrl', 'index':112}, 'destn':{'type':'INCL','mask':[4]}},
         '10':{'name':'UndS10H'  , 'marker':{'type':'ctrl', 'index':113}, 'destn':{'type':'INCL','mask':[4]}},
         '11':{'name':'UndS100H' , 'marker':{'type':'ctrl', 'index':114}, 'destn':{'type':'INCL','mask':[4]}},
         '12':{'name':'Lesa1H'   , 'marker':{'type':'ctrl', 'index':128}, 'destn':{'type':'INCL','mask':[5]}},
         '13':{'name':'Lesa10H'  , 'marker':{'type':'ctrl', 'index':129}, 'destn':{'type':'INCL','mask':[5]}},
         '14':{'name':'Lesa100H' , 'marker':{'type':'ctrl', 'index':130}, 'destn':{'type':'INCL','mask':[5]}},
         '15':{'name':'BLDH'     , 'marker':{'type':'fixed', 'index':'910kH'}, 'destn':{'type':'INCL','mask':[3]}},
         '16':{'name':'BLDS'     , 'marker':{'type':'fixed', 'index':'910kH'}, 'destn':{'type':'INCL','mask':[4]}},}

    if q is not None:
        for i,qp in q.items():
            p[str(-1-int(i))] = qp

    #  Load the beam and ctrl pattern
    dest = json.loads(open(path+'/dest.json','r').read())
    ctrl = json.loads(open(path+'/ctrl.json','r').read())

    #  Compute the triggers
    trigs      = {}
    trig_stats = {}
    for key,d in dest.items():
        td = {}
        td_stats = {}
        if key=='beams' or key=='allows':
            continue
        for i,trig in p.items():
            index = trig['marker']['index']
            if trig['marker']['type']=='fixed':
                xmark = [j for j in range(start,stop,FixedRateSync.FixedIntvsDict[index]['intv'])]
            elif trig['marker']['type']=='ac':
                xmark = [j for j in range(start,stop,1166*13*ACRateSync.ACIntvsDict[index]['intv'])]
            elif trig['marker']['type']=='ctrl':
                xmark = ctrl[str(index//CTLBITS)][str(index&(CTLBITS-1))]

            if trig['destn']['type']=='DC':
                xi = xmark
            else:
                xmask = np.full(len(d[1]),False)
                for j in trig['destn']['mask']:
                    xmask = np.logical_or( xmask, np.array(d[1])==j )
                xdest = []
                if len(xmask)>0:
                    xdest = np.array(d[0])[xmask]
                if trig['destn']['type']=='INCL':
                    xi = np.intersect1d(xmark,xdest).tolist()
                if trig['destn']['type']=='EXCL':
                    xi = np.setdiff1d  (xmark,xdest).tolist()

            diff = np.diff(xi)
            td[i] = xi
            asum = len(xi)
            amin = int(np.amin(diff,initial=910000)) if asum>1 else -1
            amax = int(np.amax(diff,initial=-1))
            afirst = xi[0] if len(xi) else -1
            alast  = xi[-1] if len(xi) else -1
            td_stats[i] = {'sum':asum, 
                           'min':amin, 
                           'max':amax, 
                           'first':afirst, 
                           'last':alast}

        trigs     [key] = td
        trig_stats[key] = td_stats

    #  Add the names
    for i,trig in p.items():
        trigs[i] = {'name':str(i)+':'+trig['name']}

    open(path+'/trig.json'      ,'w').write(json.dumps(trigs))
    open(path+'/trig_stats.json','w').write(json.dumps(trig_stats))
        
