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

#include <list>
#include <string>
#include <vector>
#include <sstream>
#include <semaphore.h>

using namespace Tpr;

static const double CLK_FREQ = 1300e6/7.;

extern int optind;

static const unsigned MAX_FRAMES=950000;

class Pattern {
public:
  Event event[MAX_FRAMES];
};

class ThreadArgs {
public:
  ThreadArgs() { sem_init(sem,0,1); }
public:
  std::list<Pattern*>    input;
  std::list<Pattern*>    output;
  sem_t*                 sem;
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

  //  This is standard setup
  reg.xbar.setEvr( XBar::StraightIn );
  reg.xbar.setEvr( XBar::StraightOut);
  reg.xbar.setTpr( XBar::StraightIn );
  reg.xbar.setTpr( XBar::StraightOut);

  reg.tpr.clkSel(true);  // LCLS2 clock
  reg.tpr.rxPolarity(false);

  //  This is channel setup for 1 MHz data streaming
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

  //  Make a queue of Pattern buffers
  ThreadArgs args;

  //  Fill the input queue
  for(unsigned i=0; i<1; i++)
    args.input.push_back(new Pattern);

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

  //  read the captured frames
  TprQueues& q = *(TprQueues*)ptr;

  char* buff = new char[32];

  int64_t allrp = q.allwp[idx];

  sem_wait(args.sem);
  Pattern* p = args.input.front();
  args.input.pop_front();
  sem_post(args.sem);

  reg.base.channel[_channel].control = 1;

  read(fd, buff, 32);

  //  capture all frames between 1Hz markers
  unsigned nframes=0;
  bool done  = false;

  do {
    while(allrp < q.allwp[idx] && !done) {
      void* hp = reinterpret_cast<void*>
        (&q.allq[q.allrp[idx].idx[allrp &(MAX_TPR_ALLQ-1)] &(MAX_TPR_ALLQ-1) ].word[0]);
      Tpr::SegmentHeader* hdr = new(hp) Tpr::SegmentHeader;
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
          memcpy(&p->event[nframes++],hdr,sizeof(Event));
        }
      }
      else if ((!acsync && (event->fixedRates&(1<<6))) ||
               ( acsync && (event->acRates   &(1<<4)))) {
        done = true;
        printf("Record finished with %u frames\n", nframes);
      }
      else if (nframes < MAX_FRAMES) {
        if (mpstst && event->mpsClass != p->event[0].mpsClass) {
          printf("MPS state change from %016llx to %016llx... restarting\n",
                 (long long unsigned)p->event[0].mpsClass, (long long unsigned)event->mpsClass);
          nframes = 0;
        }
        else
          memcpy(&p->event[nframes++],hdr,sizeof(Event));
      }
      else {
        printf("Reached MAX_FRAMES... aborting\n");
        nframes = 0;
      }
        
      allrp++;
    }
    read(fd, buff, 32);
  } while(!done);

  //  disable channel 0
  reg.base.channel[_channel].control = 0;

  //  push the buffer to processing
  sem_wait(args.sem);
  args.output.push_back(p);
  sem_post(args.sem);

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

    Pattern* p = args.output.front();
    args.output.pop_front();
    for(unsigned i=0; i<nframes; i++)
      fwrite(&p->event[i],sizeof(Event),1,f);

    fclose(f);
  }

}

