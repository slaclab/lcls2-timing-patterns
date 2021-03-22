#  Dictionary index is synonymous with beam request engine index
#  It's also synonymous with the destination index except for "keep"

dumpBSY = 4       # destination id for dump (mitigation device)
dumpBSY_keep = 15 # engine for maintaining 1Hz to dump 

def lcls_destn():
    d = {}
    d[0] = {'name':'Laser_Shutter'           ,'allow':[0]}
    d[1] = {'name':'Yag01b'                  ,'allow':[1]}
    d[2] = {'name':'Laser_Heater_Screen'     ,'allow':[2]}
    d[3] = {'name':'Diag_Line_0'             ,'allow':[3]}
    d[4] = {'name':'DumpBSY'                 ,'allow':[4]}
    d[5] = {'name':'TDUND'                   ,'allow':[4,5]}
    d[6] = {'name':'TDUNDS'                  ,'allow':[4,6]}
    d[7] = {'name':'HXR_Dump'                ,'allow':[4,5,7]}
    d[8] = {'name':'SXR_Dump'                ,'allow':[4,6,8]}
    d[15] = {'name':'DumpBSY_keep'           ,'allow':[4], 'nogen':True}
    return d
