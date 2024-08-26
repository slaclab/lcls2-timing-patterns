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

#include "pattdata.hh"

#include <list>
#include <string>
#include <vector>
#include <sstream>

using namespace Patt;

extern int optind;

static void usage(const char* p) {
  printf("Usage: %s -f <directory> [options]\n",p);
  printf("Options:\n");
  printf("  -b <buckets>  # of buckets to dump\n");
  printf("  -c <class>    beam class for all dest\n");
  printf("  -l <buckets>  # of buckets per print line\n");
}

int main(int argc, char** argv) {
  
  extern char* optarg;
  int c;
  unsigned nbkts=910000;
  unsigned bclas=2;
  unsigned ndest=2;
  unsigned lbkts=80;
  const char* fname = 0;
  while ( (c=getopt( argc, argv, "b:c:d:f:l:h?")) != EOF ) {
    switch(c) {
    case 'b': nbkts = strtoul(optarg, NULL, 0); break;
    case 'c': bclas = strtoul(optarg, NULL, 0); break;
    case 'd': ndest = strtoul(optarg, NULL, 0); break;
    case 'f': fname = optarg; break;
    case 'l': lbkts = strtoul(optarg, NULL, 0); break;
    case 'h':
    case '?':
    default:
      usage(argv[0]);
      exit(0);
    }
  }


  //  Set all destinations to beam class bclas
  BeamClassType bclass(ndest);
  for(unsigned i=0; i<ndest; i++)
    bclass[i]=bclas;

  //  Setup printout format
  char* BKT_HDR = new char[lbkts+2];
  for(unsigned i=0; i<lbkts; i++)
    BKT_HDR[i] = '0'+(i%10);
  BKT_HDR[lbkts]='\n';
  BKT_HDR[lbkts+1]=0;
  char line[lbkts+2]; line[lbkts]='\n'; line[lbkts+1]=0;

  // dest.json
  { 
    DestPatternSet     dest_patt(std::string(fname)+"/dest.json");
    const DestPatternType& p = dest_patt.pattern(bclass);
    for(unsigned i=0; i<nbkts; ) {
      for(unsigned j=0; j<lbkts; i++,j++) {
        if (i==nbkts) {
          //        BKT_HDR[j]='\n';
          line   [j]='\n';
          line   [j+1]=0;
          break;
        }
        if (p[i]==NO_DEST)
          line[j]='-';
        else
          line[j]=(char)('0'+p[i]);
      }
      printf(BKT_HDR);
      printf(line);
    }
  }

  // dest_stats.json
  {
    DestPatternStatSet dest_stat(std::string(fname)+"/dest_stats.json");
    printf("DST | FIRST |  LAST |  MIN  |  MAX  |  SUM  |\n");
    for(unsigned d=0; d<ndest; d++) {
      const PatternStat& s = dest_stat.stat(bclass,d);
      printf("  %u | %6d| %6d| %6d| %6d| %6d|\n",
             d, s.first, s.last, s.min, s.max, s.sum);
    }
  }

  // ctrl.json
  {
    char* BITS = "-123456789abcdef";
    char lines[4][lbkts+2];
    for(unsigned k=0; k<4; k++) {
      lines[k][lbkts]='\n';
      lines[k][lbkts+1]=0;
    }
    SeqPatternSet      seq_patt (std::string(fname)+"/ctrl.json");
    const SeqPatternType& p = seq_patt.seq(0);
    for(unsigned i=0; i<nbkts; ) {
      for(unsigned j=0; j<lbkts; i++,j++) {
        if (i==nbkts) {
          //        BKT_HDR[j]='\n';
          for(unsigned k=0; k<4; k++) {
            lines[k][j+0]='\n';
            lines[k][j+1]=0;
          }
          break;
        }
        for(unsigned k=0; k<4; k++) 
          lines[k][j] = BITS[(p[i]>>(4*k))&0xf];
      }
      printf(BKT_HDR);
      for(unsigned k=0; k<4; k++)
        printf(lines[k]);
    }
  }

  //  ctrl_stats.json
  {
    SeqPatternStatSet  seq_stat (std::string(fname)+"/ctrl_stats.json");
    printf("BIT | FIRST |  LAST |  MIN  |  MAX  |  SUM  |\n");
    for(unsigned d=0; d<16; d++) {
      const PatternStat& s = seq_stat.stat(d,0);
      printf(" %2u | %6d| %6d| %6d| %6d| %6d|\n",
             d, s.first, s.last, s.min, s.max, s.sum);
    }
  }

}
