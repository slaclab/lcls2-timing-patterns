//
//  Command-line driver of TPR configuration
//
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <time.h>
#include <stdio.h>

#include "tpr.hh"
#include "tprsh.hh"
#include "tprdata.hh"

#include <string>
#include <vector>
#include <sstream>

using namespace Tpr;

static const double CLK_FREQ = 1300e6/7.;

extern int optind;

class BeamStat {
public:
  BeamStat() : sum(0), minspacing(-1), maxspacing(-1), first(-1), last(-1) {}
public:
  void request(unsigned bucket) {
    sum++;
    if (first < 0) {
      first = bucket;
    }
    else {
      int spacing = bucket - last;
      if (minspacing < 0 || spacing < minspacing)
        minspacing = spacing;
      if (spacing > maxspacing)
        maxspacing = spacing;
    }
    last = bucket;
  }
public:
  unsigned sum;
  int      minspacing;
  int      maxspacing;
  int      first;
  int      last;
};

static void usage(const char* p) {
  printf("Usage: %s -d <device> [options]\n",p);
  printf("Options: -d <device>   : open device (default: /dev/tpra)\n");
  printf("         -f <filename> : record frame capture to file\n");
  printf("         -a            : capture 1Hz AC (default: CW)\n");
  printf("         -m            : require no MPS changes\n");
}

int main(int argc, char** argv) {

  extern char* optarg;
  int c;
  const char* fname = 0;
  const char* dname = "/dev/tpra";
  bool        acsync = false;
  bool        mpstst = false;
  while ( (c=getopt( argc, argv, "amd:f:h?")) != EOF ) {
    switch(c) {
    case 'a': acsync = true; break;
    case 'm': mpstst = true; break;
    case 'd': dname = optarg; break;
    case 'f': fname = optarg; break;
    case 'h':
    case '?':
    default:
      usage(argv[0]);
    exit(0);
    }
  }

  printf("Using tpr %s\n",dname);

  int fd = open(dname, O_RDWR);
  if (fd<0) {
    perror("Could not open");
    return -1;
  }

  void* ptr = mmap(0, sizeof(TprReg), PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
  if (ptr == MAP_FAILED) {
    perror("Failed to map");
    return -2;
  }

  TprReg& reg = *reinterpret_cast<TprReg*>(ptr);
  printf("FpgaVersion: %08X\n", reg.version.FpgaVersion);
  printf("BuildStamp: %s\n", reg.version.buildStamp().c_str());

  reg.xbar.setEvr( XBar::StraightIn );
  reg.xbar.setEvr( XBar::StraightOut);
  reg.xbar.setTpr( XBar::StraightIn );
  reg.xbar.setTpr( XBar::StraightOut);

  reg.tpr.clkSel(true);  // LCLS2 clock
  reg.tpr.rxPolarity(false);

  int idx=0;
  char dev[16];
  sprintf(dev,"%s%u",dname,idx);

  fd = open(dev, O_RDONLY);
  if (fd<0) {
    printf("Open failure for dev %s [FAIL]\n",dev);
    perror("Could not open");
    exit(1);
  }

  ptr = mmap(0, sizeof(TprQueues), PROT_READ, MAP_SHARED, fd, 0);
  if (ptr == MAP_FAILED) {
    perror("Failed to map - FAIL");
    exit(1);
  }

  unsigned _channel = 0;
  reg.base.setupTrigger(_channel,
                        _channel,
                        0, 0, 1, 0);
  unsigned ucontrol = reg.base.channel[_channel].control;
  reg.base.channel[_channel].control = 0;

  unsigned urate   = 0; // max rate
  unsigned destsel = 1<<17; // BEAM - DONT CARE
  reg.base.channel[_channel].evtSel = (destsel<<13) | (urate<<0);
  reg.base.channel[_channel].bsaDelay = 0;
  reg.base.channel[_channel].bsaWidth = 1;
  reg.base.channel[_channel].control = ucontrol | 1;

  //  read the captured frames
  TprQueues& q = *(TprQueues*)ptr;

  char* buff = new char[32];

  int64_t allrp = q.allwp[idx];

  read(fd, buff, 32);

  //  capture all frames between 1Hz markers
  unsigned nframes=0;
  const unsigned MAX_FRAMES = 950000;
  Event* events = new Event[MAX_FRAMES];
    
  bool done  = false;

  do {
    while(allrp < q.allwp[idx] && !done) {
      void* p = reinterpret_cast<void*>
        (&q.allq[q.allrp[idx].idx[allrp &(MAX_TPR_ALLQ-1)] &(MAX_TPR_ALLQ-1) ].word[0]);
      Tpr::SegmentHeader* hdr = new(p) Tpr::SegmentHeader;
      if (nframes && hdr->drop()) {
        printf("Dropped frame during capture... restart\n");
        nframes = 0;
      }
      while(hdr->type() != Tpr::_Event )
        hdr = hdr->next();
      Tpr::Event* event = new(hdr) Tpr::Event;

      if (nframes==0) {
        if ((!acsync && (event->fixedRates&(1<<6))) ||
            ( acsync && (event->acRates   &(1<<4)))) {
          printf("Record started\n");
          memcpy(&event[nframes++],hdr,sizeof(Event));
        }
      }
      else if ((!acsync && (event->fixedRates&(1<<6))) ||
               ( acsync && (event->acRates   &(1<<4)))) {
        done = true;
        printf("Record finished with %u frames\n", nframes);
      }
      else if (nframes < MAX_FRAMES) {
        if (mpstst && event[nframes].mpsClass != event[0].mpsClass) {
          printf("MPS state change from %016llx to %016llx... restarting\n",
                 (long long unsigned)event[0].mpsClass, (long long unsigned)event[nframes].mpsClass);
          nframes = 0;
        }
        else
          memcpy(&event[nframes++],hdr,sizeof(Event));
      }
      else {
        printf("Reached MAX_FRAMES... aborting\n");
        done = true;
      }

      allrp++;
    }
    read(fd, buff, 32);
  } while(!done);
    
  //  disable channel 0
  reg.base.channel[_channel].control = 0;
  munmap(ptr, sizeof(TprQueues));
  close(fd);

  //  Recording
  if (fname) {
    printf("Opening file %s\n",fname);
    FILE* f = fopen(fname,"w");
    if (!f) {
      printf("Open failure for output file %s [FAIL]\n",fname);
      perror("Open failed");
      exit(1);
    }

    for(unsigned i=0; i<nframes; i++)
      fwrite(&events[i],sizeof(Event),1,f);

    fclose(f);
  }

  //  Processing?
  {
    //  Summarize beam requests for each destination
    BeamStat* stats = new BeamStat[16];
    uint64_t pulseId0 = events[0].pulseId;
    for(unsigned i=0; i<nframes; i++) {
      unsigned bucket = events[i].pulseId - pulseId0;
      if (events[i].beamReq)
        stats[events[i].destn].request(bucket);
    }

    printf("-------------------------------------------------------\n");
    printf(" DST | PC  |  Sum   |  Min   |  Max   | First  | Last  \n");
    printf("-------------------------------------------------------\n");
    for(unsigned i=0; i<16; i++) {
      if (stats[i].last >= 0)
        printf("  %2d |  %2d | %6d | %6d | %6d | %6d | %6d \n",
               i, unsigned((events[0].mpsClass>>(4*i))&0xf),
               stats[i].sum, stats[i].minspacing, stats[i].maxspacing,
               stats[i].first, stats[i].last);
    }               
    printf("-------------------------------------------------------\n");
        
  }  

  delete[] events;
}

