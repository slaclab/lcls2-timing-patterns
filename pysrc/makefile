CCACHE_DISABLE=1

CPSW_DIR=/afs/slac/g/lcls/package/cpsw/framework/R4.4.1/src

SRCDIR=.
-include $(SRCDIR)/release.mak

include $(CPSW_DIR)/defs.mak

INSTALL_DIR=../

INCLUDE_DIRS += /afs/slac/g/lcls/package/anaconda/envs/python3_env/include/python3.8
pyseqsim_SRCS = pyseqsim.cc
SHARED_LIBRARIES+=pyseqsim
LIBRARY_LINKS = $(SHARED_LIBRARIES:%=%.so)
TGTS += $(LIBRARY_LINKS)

$(LIBRARY_LINKS): $(SHARED_LIBRARIES:%=lib%.so)
	ln -s $< $@

include $(CPSW_DIR)/rules.mak

clean:
	rm -f *.o
	rm -f $(LIBRARY_LINKS)
	rm -f $(SHARED_LIBRARIES:%=lib%.so)

