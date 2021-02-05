CCACHE_DISABLE=1


CPSW_DIR=/afs/slac/g/lcls/package/cpsw/framework/R4.4.1/src
BSA_DIR=/afs/slac/g/lcls/package/timing/bsa
BSA_VERSION=R1.2.0
BSA=$(BSA_DIR)/$(BSA_VERSION)

# may override CPSW_DIR / DEVICELIB_DIR from release.mak
# must set SRCDIR (is redefined by recursive make)
SRCDIR=.
-include $(SRCDIR)/release.mak

include $(CPSW_DIR)/defs.mak

LDFLAGS+= -Wl,-Bstatic -static-libgcc
LDFLAGS+=-L$(BSA)/$(TARCH)/lib

INCLUDE_DIRS += $(BSA)/$(TARCH)/include
INSTALL_DIR=../

HEADERS  = tpr.hh tprsh.hh tprdata.hh

tpr_SRCS  = tpr.cc

STATIC_LIBRARIES+=tpr

tpr_record_SRCS = tpr_record.cc tpr.cc
tpr_record_LIBS = pthread rt dl
PROGRAMS    += tpr_record

include $(CPSW_DIR)/rules.mak
