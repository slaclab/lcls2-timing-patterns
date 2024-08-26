#ifndef pyseqsim_hh
#define pyseqsim_hh

#include <vector>
#include <map>

class stats_s {
public:
  stats_s() : sum(0), min(-1), max(-1), first(-1), last(-1) {}
public:
  unsigned sum;
  int      min;
  int      max;
  int      first;
  int      last;
};

class xy_s {
public:
  xy_s(unsigned _x, unsigned _y) : x(_x), y(_y) {}
public:
  unsigned x;
  unsigned y;
};

typedef struct {
  PyObject_HEAD
  unsigned start;
  unsigned stop;
  bool     acmode;
} beamseq;

typedef std::vector<unsigned> xdata_s;

typedef struct {
  PyObject_HEAD
  unsigned start;
  unsigned stop;
  bool     acmode;
} controlseq;

#endif
