#include "pattdata.hh"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

using namespace Patt;

static std::vector<unsigned> read_vector(const char*& p)
{
  p++;  // skip opening ( or [
  std::vector<unsigned> v;
  if (!(*p==')' || *p==']')) {  // non-empty vector
    for(unsigned i=0; (1); i++) {
      char* q;
      v.push_back(strtoul(p, &q, 10));
      p = q;
      if (*p != ',') break;
      p++;
    }
  }
  p++;  // skip closing ) or ]
  return v;
}

#define GETINT(TITLE) {                                         \
    int nch = strlen(#TITLE);                                   \
    char* q;                                                    \
    if (strncmp(p,#TITLE,nch)==0) {                             \
      s.TITLE = strtol(p+nch+2,&q,10);                          \
      p=q;                                                      \
    }                                                           \
}

DestPatternSet::DestPatternSet(std::string fname)
{
  FILE* f = fopen(fname.c_str(),"r");
  if (!f) {
    throw std::string("Could not open file ")+fname;
  }

  const unsigned max_size = 12*1024*1024;
  char* buff = new char[max_size];
  size_t len = fread(buff, 1, max_size, f);
  fclose(f);

  const char* p = buff;
  while(*p++ != '{') ;
  while(1) {
    while(*p++ != '\"') ;
    BeamClassType beamclass = read_vector(p);
    while(*p++ != ':') ;
    while(*p++ != '[') ;
    std::vector<unsigned> xdata = read_vector(p);
    while(*p != '[') p++;
    std::vector<unsigned> ydata = read_vector(p);
    //  Map it
    { DestPatternType patt(MAX_FRAMES);
      for(unsigned i=0; i<MAX_FRAMES; i++)
        patt[i] = NO_DEST;
      for(unsigned i=0; i<xdata.size(); i++)
        patt[xdata[i]] = ydata[i];
      _patterns[beamclass] = patt; }
    while(*p++ != ']') ;
    if (*p!=',') break;
  }
}

const DestPatternType& DestPatternSet::pattern(const BeamClassType& beamClass)
{
  return _patterns[beamClass];
}

DestPatternStatSet::DestPatternStatSet(std::string fname)
{
  FILE* f = fopen(fname.c_str(),"r");
  if (!f) {
    throw std::string("Could not open file ")+fname;
  }

  const unsigned max_size = 12*1024*1024;
  char* buff = new char[max_size];
  size_t len = fread(buff, 1, max_size, f);
  fclose(f);
  
  const char* p = buff;
  while(*p++ != '{') ;
  while(1) {
    while(*p++ != '\"') ;
    BeamClassType beamclass = read_vector(p);
    std::vector<PatternStat> ps;
    while(*p++ != ':') ;
    while(*p++ != '[') ;
    do {
      PatternStat s;
      do {
        while(*p++ != '\"') ;
        GETINT(max);
        GETINT(min);
        GETINT(first);
        GETINT(last);
        GETINT(sum);
      } while(*p++==',');
      ps.push_back(s);
    } while(*p++==',');
    _stats[beamclass] = ps;
    if (*p++!=',') break;
  }
}

const PatternStat& DestPatternStatSet::stat(const BeamClassType beamclass,
                                            unsigned dest)
{
  return _stats[beamclass][dest];
}

SeqPatternSet::SeqPatternSet(std::string fname)
{
  FILE* f = fopen(fname.c_str(),"r");
  if (!f) {
    throw std::string("Could not open file ")+fname;
  }

  const unsigned max_size = 12*1024*1024;
  char* buff = new char[max_size];
  size_t len = fread(buff, 1, max_size, f);
  fclose(f);
  
  const char* p = buff;
  while(*p++ != '{') ;
  while(1) {  // loop over engines
    while(*p++ != '\"') ;
    char* q;
    unsigned eng = strtoul(p, &q, 10);
    //  initialize buckets for engine
    _seqs[eng] = SeqPatternType(MAX_FRAMES);
    p = q;
    while(*p++ != ':') ;
    while(1) {  // loop over bits
      while(*p++ != '\"') ;
      unsigned bit = strtoul(p, &q, 10);
      p = q;
      while(*p != '[') p++;
      std::vector<unsigned> xdata = read_vector(p);
      // Add to map
      for(unsigned i=0; i<xdata.size(); i++)
        _seqs[eng][xdata[i]] |= (1<<bit);
      if (*p!=',') break;
    }
    p++;  // skip over }
    if (*p!=',') break;
  }
}

const SeqPatternType& SeqPatternSet::seq(unsigned eng)
{
  return _seqs[eng];
}

SeqPatternStatSet::SeqPatternStatSet(std::string fname)
{
  FILE* f = fopen(fname.c_str(),"r");
  if (!f) {
    throw std::string("Could not open file ")+fname;
  }

  const unsigned max_size = 12*1024*1024;
  char* buff = new char[max_size];
  size_t len = fread(buff, 1, max_size, f);
  fclose(f);
  
  const char* p = buff;
  while(*p++ != '{') ;
  while(1) {  // loop over engine
    while(*p++ != '\"') ;
    char* q;
    unsigned eng = strtoul(p, &q, 10);
    p = q;
    while(*p++ != ':') ;
    std::map<unsigned,PatternStat> ps;
    while(1) {  // loop over bits
      while(*p++ != '\"') ;
      unsigned bit = strtoul(p, &q, 10);
      p = q;
      while(*p++ != '{');
      PatternStat s;
      do {
        while(*p++ != '\"') ;
        GETINT(max);
        GETINT(min);
        GETINT(first);
        GETINT(last);
        GETINT(sum);
      } while(*p++==',');
      ps[bit] = s;
      if (*p++!=',') break;
    }
    // Add to map
    _stats[eng] = ps;
    if (*p!=',') break;
  }
}

const PatternStat& SeqPatternStatSet::stat(unsigned eng,
                                           unsigned bit)
{
  return _stats[eng][bit];
}
