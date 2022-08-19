export PYTHONPATH=
source /afs/slac/g/lcls/tools/script/ENVS.bash
source /afs/slac/g/lcls/epics/setup/epicsenv-7.0.3.1-1.0.bash
source $TOOLS/script/use_pydm.sh 
export PYDM_STYLESHEET="/afs/slac/g/lcls/tools/pydm/stylesheet/default.qss"
#  Need to point python to pick up the c module
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH=${PYTHONPATH}:${DIR}/pysrc:.