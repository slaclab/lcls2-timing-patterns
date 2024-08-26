#ifndef pattdata_hh
#define pattdata_hh

#include <stdint.h>
#include <map>
#include <string>
#include <vector>

namespace Patt {
  //  Maximum frames in interval between 1Hz markers (fixed/AC)
  //  1Hz fixed markers are exactly 910000
  //  which is like 60*0.91/(1300/1400) or 58.8 Hz
  static const unsigned MAX_FRAMES = 910000;
  static const unsigned MAX_DEST = 16;
  static const unsigned MAX_CTRL = 18;
  static const uint8_t  NO_DEST = 0xff;

  // maps of bucket to ...
  //  typedef std::map<unsigned,uint8_t > DestPatternType;  // destination
  //  typedef std::map<unsigned,uint16_t> SeqPatternType;   // sequence bitmask
  // vector access should be faster for worst case
  // vector size is MAX_FRAMES
  typedef std::vector<uint8_t>        DestPatternType;
  typedef std::vector<uint16_t>       SeqPatternType;

  typedef std::vector<unsigned>       BeamClassType;

  class PatternStat {
  public:
    PatternStat() : first(0), last(0), min(0), max(0), sum(0) {}
  public:
    int      first;
    int      last;
    int      min;
    int      max;
    unsigned sum;
  };

  class DestPatternSet {
  public:
    DestPatternSet(std::string);
  public:
    const DestPatternType& pattern(const BeamClassType&);
  private:
    unsigned _ndest;
    std::map<BeamClassType,DestPatternType> _patterns;
  };

  class DestPatternStatSet {
  public:
    DestPatternStatSet(std::string);
  public:
    const PatternStat& stat(const BeamClassType,
                            unsigned dest);
  private:
    unsigned _ndest;
    std::map< BeamClassType, std::vector<PatternStat> > _stats;
  };

  class SeqPatternSet {
  public:
    SeqPatternSet(std::string);
  public:
    unsigned nengines() const { return _neng; }
    const SeqPatternType& seq(unsigned eng);
  private:
    unsigned _neng;
    std::map<unsigned,SeqPatternType> _seqs;
  };

  class SeqPatternStatSet {
  public:
    SeqPatternStatSet(std::string);
  public:
    unsigned nengines() const { return _neng; }
    const PatternStat& stat(unsigned eng,
                            unsigned bit);
  private:
    unsigned _neng;
    std::map<unsigned, std::map<unsigned, PatternStat> > _stats;
  };
};

#endif
