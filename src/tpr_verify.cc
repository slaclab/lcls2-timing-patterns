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
#include <signal.h>

#include "tpr.hh"
#include "tprsh.hh"
#include "tprdata.hh"
#include "pattdata.hh"

#include <list>
#include <string>
#include <vector>
#include <sstream>
#include <semaphore.h>

using namespace Tpr;
using namespace Patt;

static const double CLK_FREQ = 1300e6/7.;

static bool lverbose = false;

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
  const char*            fname;
};

//  1Hz Processing thread
static void* process(void* args) {
  ThreadArgs *t = (ThreadArgs*)args;

  //  Load the target pattern
  //  dest.json, dest_stats.json, ctrl.json, ctrl_stats.json
  DestPatternSet     dest_patt(std::string(t->fname)+"/dest.json");
  DestPatternStatSet dest_stat(std::string(t->fname)+"/dest_stats.json");
  SeqPatternSet      seq_patt (std::string(t->fname)+"/ctrl.json");
  SeqPatternStatSet  seq_stat (std::string(t->fname)+"/ctrl_stats.json");

  if (lverbose)
    printf("Waiting for input\n");

  while(1) {
    // wait for input
    if (t->output.empty()) {
      usleep(10000);
      continue;
    }

    //  Get the next record
    sem_wait(t->sem);
    Pattern* p = t->output.front();
    t->output.pop_front();
    sem_post(t->sem);

    if (lverbose)
      printf("Processing record\n");

    //  Process the record
    do {
      const unsigned nframes = MAX_FRAMES;  // what to do in AC mode?
      const Event* events = p->event;
      //  Summarize beam requests for each destination
      BeamStat* stats = new BeamStat[MAX_DEST];
      BeamStat* cstat = new BeamStat[MAX_CTRL*16];
      uint64_t pulseId0 = events[0].pulseId;

      //  Beam class should be static
      BeamClassType bclass(MAX_DEST);
      for(unsigned i=0; i<MAX_DEST; i++)
        bclass[i] = (events[0].mpsClass>>(4*i))&0xf;

      if (lverbose) 
        printf("bclass %016llx\n", events[0].mpsClass);

      const DestPatternType& dp = dest_patt.pattern(bclass);

      for(unsigned i=0; i<nframes; i++) {
        unsigned bucket = events[i].pulseId - pulseId0;
        //  Check destination match
        uint8_t destn = events[i].beamReq ? events[i].destn : NO_DEST;
        if (dp.size() && destn!=dp[i]) { // mismatch
          printf("BKT %6u:  dest %2x  exp %2x\n",
                 i,destn,dp[i]);
        }
        //  Accumulate destination stats
        if (events[i].beamReq)
          stats[events[i].destn].request(bucket);
        //  Check sequence match
        for(unsigned e=0; e<seq_patt.nengines(); e++) {
          const SeqPatternType & sp = seq_patt.seq(e);
          if (events[i].control[e]!=sp[i]) {
            printf("BKT %6u: ctrl %2d.%02x  exp %02x\n",
                   i, e, events[i].control[e], sp[i]);
          }
          //  Accumulate sequence stats
          uint16_t m=events[i].control[e];
          for(unsigned b=0; m; b++) {
            if (m&1) 
              cstat[e*16+b].request(bucket);
            m >>= 1;
          }
        }
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
        
    } while(0);  

    //  Release the record
    sem_wait(t->sem);
    t->input.push_back(p);
    sem_post(t->sem);
  }

  return 0;
}

static void usage(const char* p) {
  printf("Usage: %s -d <device> [options]\n",p);
  printf("Options: -d <device>   : open device (default: /dev/tpra)\n");
  printf("         -f <filename> : target pattern\n");
  printf("         -a            : capture 1Hz AC (default: CW)\n");
  printf("         -m            : require no MPS changes\n");
}

static TprReg* _reg = 0;
static int idx = 11;

static void sigHandler( int signal ) 
{
  psignal(signal, "sigHandler received signal");

  //  Dump
  if (_reg) {
    _reg->csr.dump();
    _reg->base.dump();

    _reg->base.channel[idx].control = 0;
  }

  ::exit(signal);
}

int main(int argc, char** argv) {

  extern char* optarg;
  int c;
  const char* fname = 0;
  const char* dname = "/dev/tpra";
  bool        acsync = false;
  bool        mpstst = false;
  while ( (c=getopt( argc, argv, "amd:f:vh?")) != EOF ) {
    switch(c) {
    case 'a': acsync = true; break;
    case 'm': mpstst = true; break;
    case 'd': dname = optarg; break;
    case 'f': fname = optarg; break;
    case 'v': lverbose = true; break;
    case 'h':
    case '?':
    default:
      usage(argv[0]);
    exit(0);
    }
  }

  struct sigaction sa;
  sa.sa_handler = sigHandler;
  sa.sa_flags = SA_RESETHAND;

  sigaction(SIGINT ,&sa,NULL);
  sigaction(SIGABRT,&sa,NULL);
  sigaction(SIGKILL,&sa,NULL);
  sigaction(SIGSEGV,&sa,NULL);

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

  TprReg& reg = *(_reg = reinterpret_cast<TprReg*>(ptr));
  printf("FpgaVersion: %08X\n", reg.version.FpgaVersion);
  printf("BuildStamp: %s\n", reg.version.buildStamp().c_str());

  //  This is standard setup
  reg.xbar.setEvr( XBar::StraightIn );
  reg.xbar.setEvr( XBar::StraightOut);
  reg.xbar.setTpr( XBar::StraightIn );
  reg.xbar.setTpr( XBar::StraightOut);

  reg.tpr.clkSel(true);  // LCLS2 clock
  reg.tpr.rxPolarity(false);
  usleep(1000000);
  reg.tpr.resetCounts();

  for(unsigned i=0; i<14; i++)
    reg.base.channel[i].control = 0;

  reg.base.channel[idx].control = 0;
  reg.base.channel[idx].evtSel  = (1<<30) | 0;
  reg.base.channel[idx].control = 1;

  usleep(2000000);

  if (lverbose) {
    printf("TPR programmed\n");
    reg.tpr.dump();
    reg.csr.dump();
    reg.base.dump();
  }

  //  Make a queue of Pattern buffers
  ThreadArgs args;
  args.fname = fname;

  //  Fill the input queue
  for(unsigned i=0; i<1; i++)
    args.input.push_back(new Pattern);

  //  Launch the thread to handle processing
  { pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_t thr;
    if (pthread_create(&thr, &attr, process, &args)) {
      perror("Error creating process thread");
      return -1;
    }
  }

  char dev[16];
  sprintf(dev,"%s%x",dname,idx);

  int fds = open(dev, O_RDONLY);
  if (fds<0) {
    printf("Open failure for dev %s [FAIL]\n",dev);
    perror("Could not open");
    exit(1);
  }

  ptr = mmap(0, sizeof(TprQueues), PROT_READ, MAP_SHARED, fds, 0);
  if (ptr == MAP_FAILED) {
    perror("Failed to map - FAIL");
    exit(1);
  }

  //  read the captured frames
  TprQueues& q = *(TprQueues*)ptr;

  char* buff = new char[32];

  int64_t allrp = q.allwp[idx];
  
  if (lverbose)
      printf("allrp %llx\n",allrp);

  while(1) {
    if (args.input.empty()) {
      usleep(10000);
      continue;
    }

    sem_wait(args.sem);
    Pattern* p = args.input.front();
    args.input.pop_front();
    sem_post(args.sem);

    if (lverbose)
      printf("Capturing\n");

    //  enable channel
    reg.base.channel[idx].control = 5;

    read(fds, buff, 32);
    
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
      read(fds, buff, 32);  // why does this read not update q.allwp[idx]
    } while(!done);

    //  disable channel 0
    reg.base.channel[idx].control = 0;

    //  push the buffer to processing
    sem_wait(args.sem);
    args.output.push_back(p);
    sem_post(args.sem);
  }

  munmap(ptr, sizeof(TprQueues));
  close(fd);
  close(fds);
}

