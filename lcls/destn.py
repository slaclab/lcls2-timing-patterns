#  Dictionary index is synonymous with beam request engine index
#  It's also synonymous with the destination index except for "keep"

dumpBSY = 2       # destination id for dump (mitigation device)
dumpBSY_keep = 15 # engine for maintaining 1Hz to dump 

def lcls_destn():
    d = {}
    d[0] = {'name':'0 SC1 Laser'           ,'allow':[0]}
    d[1] = {'name':'1 SC1 DIAG0'           ,'allow':[1]}
#    d[2] = {'name':'2 SC1 DUMPBSY'         ,'allow':[2,0]}
    d[2] = {'name':'2 SC1 DUMPBSY'         ,'allow':[2]}
    d[3] = {'name':'3 SC1 DUMPHXR'         ,'allow':[2,3]}
    d[4] = {'name':'4 SC1 DUMPSXR'         ,'allow':[2,4]}
    d[5] = {'name':'5 SC1 LESA'            ,'allow':[2,5]}
    d[15] = {'name':'15 DumpBSY_keep'           ,'allow':[2], 'nogen':True}
    return d
