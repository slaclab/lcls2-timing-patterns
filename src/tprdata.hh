#ifndef TprData_hh
#define TprData_hh

#include <bitset>

namespace Tpr {
  enum SegmentType { _Event=0, _BsaControl=1, _BsaChannel=2, _End=15 }; 
  enum TimingSource { LCLS2=0, LCLS1=1 };

  class BsaChannel {
  public:
    uint16_t reserved;
    uint16_t headerTag; // BsaChannel tag
    uint64_t pulseId;
    uint64_t newActive;
    uint64_t newAvgDone;
    uint64_t timeStamp;
    uint64_t newDone;
  };

  class BsaControl {
  public:
    uint16_t reserved;
    uint16_t headerTag;  // BsaControl tag
    uint64_t pulseId;
    uint64_t timeStamp;
    uint64_t init;
    uint64_t active;  // init AND active
    uint64_t avgdone; // init AND avgdone
  };

  class Event {
  public:
    uint16_t channels;
    uint16_t headerTag; // EventTag
    //    uint32_t words[21]; // toSlvNoBsa
    uint64_t pulseId;
    uint64_t timeStamp;
    unsigned fixedRates : 10, acRates : 6, acTimeSlots : 6, acTimeSlotPhase : 9, resync : 1;
    unsigned beamReq : 1, : 3, destn : 4, : 8, charge : 16;
    uint16_t beamEnergy[4];
    uint16_t photonWavelen[2];
    uint16_t reserved;
    uint16_t mpsLimit;
    //    bitset<4> mpsClass[16];
    uint64_t mpsClass;
    uint16_t control[18];
  };

  class BsaSummary {
  public:
    uint16_t channels;
    uint16_t headerTag;
    uint64_t pulseId;
    uint64_t newActive;
    uint64_t newAvgDone;
    uint64_t timeStamp;
    uint64_t newDone;
  };

  class SegmentHeader {
  public:
    SegmentType    type  () const { return SegmentType(_data>>16); }
    TimingSource   source() const { return TimingSource((_data>>22)&1); }
    bool           drop  () const { return (_data>>23)&1; }
    SegmentHeader* next() const { 
      unsigned offset(0);
      switch(type()) {
      case _Event     : offset=sizeof(Event); break;
      case _BsaControl: offset=sizeof(BsaControl); break;
      case _BsaChannel: offset=sizeof(BsaChannel); break;
      case _End       : return 0;
      default: break;
      }
      return reinterpret_cast<SegmentHeader*>((char*)this+offset);
    }
  private:
    uint32_t _data;
  };

};

#endif
