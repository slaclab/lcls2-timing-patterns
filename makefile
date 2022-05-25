TOPTARGETS := all clean install uninstall
SUBDIRS := src pysrc

$(TOPTARGETS): $(SUBDIRS)

$(SUBDIRS):
	cd $@ && $(MAKE) $(MAKECMDGOALS)

.PHONY: $(TOPTARGETS) $(SUBDIRS) 
