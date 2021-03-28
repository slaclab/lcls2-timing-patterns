
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <netinet/in.h> 
#include <arpa/inet.h>
#include <signal.h>
#include <new>

#include "Reg.hh"

#include <string>

static bool verbose = false;

class MpsSim {
public:
  unsigned latchDiag() const { return unsigned(_csr)&1; }
  unsigned tag      () const { return unsigned(_tag_ts)&0xffff; }
  unsigned timestamp() const { return (unsigned(_tag_ts)>>16)&0xffff; }
  unsigned pclass   (unsigned i) const
  { 
    return (unsigned(_pclass[i/4])>>(8*(i&3)))&0xf; 
  }
  void setLatch(bool v) 
  { 
    if (v) _csr.setBit(0);
    else   _csr.clearBit(0);
  }
  void setStrobe() { _csr.setBit(31); }
  void setTag   (unsigned t) { 
    unsigned v = _tag_ts;
    v &= ~0xffff;
    v |= (t&0xffff);
    _tag_ts = v;
  }
  void setClass(unsigned d,
                unsigned c)
  {
    unsigned v = _pclass[d/4];
    v &= ~((0xff)<<(8*(d&3)));
    v |= (c&0xff)<<(8*(d&3));
    _pclass[d/4] = v;
  }
  void process(unsigned dst,
               unsigned pc,
               bool     latch_tag)
  {
    if (dst >= 0)
      setClass(dst,pc);

    setTag  (latch_tag);
    setLatch(latch_tag != 0);

    if (latch_tag || (dst>=0))
      setStrobe();

    if (verbose)
      printf("process done\n");
  }
  int handle_data(int fd) {
    unsigned buff[32];
    char* b = reinterpret_cast<char*>(&buff);
    int rem=4;
    do {
      int r = read(fd,b,rem);
      if (verbose)
        printf("read %d bytes\n",r);
      if (r<=0) return -1;
      rem -= r;
      b   += r;
    } while (rem>0);
    for(unsigned i=0; rem<=0; i++, rem+=4) {
      unsigned dst = buff[i]&0xff;
      unsigned pc  = (buff[i]>>8)&0xff;
      bool latch_tag = buff[i] & (1<<31);
      printf("Received cmd 0x%x: dst %u pc %u latch %c\n",
             buff[i],dst,pc,latch_tag ? 'Y':'N');
      process(dst,pc,latch_tag);
      write(fd,&buff[i],4);
    }
    return 0;
  }
  void dump() {
    printf("csr: %08x\n",unsigned(_csr));
    printf("tag: %08x\n",unsigned(_tag_ts));
    printf("pc0: %08x\n",unsigned(_pclass[0]));
    printf("pc1: %08x\n",unsigned(_pclass[1]));
  }
private:
  Pds::Cphw::Reg _csr;
  Pds::Cphw::Reg _tag_ts;
  uint32_t       _reserved[2];
  Pds::Cphw::Reg _pclass[2];
};


void usage(const char* p) {
  printf("Usage: %s [options]\n",p);
  printf("Options: -a <IP addr (dotted notation)> : Use network <IP>\n");
  printf("         -p <tcp port>                  : Open a TCP port for receiving MPS changes\n");
  printf("         -C <dst,class>                 : Set MPS dest to power class\n");
  printf("         -L <tag>                       : Latch with tag\n");
  printf("         -v                             : set verbose\n");
}

int main(int argc, char** argv) {

  const char* ip = "192.168.2.10";
  char* endptr = 0;

  unsigned latch_tag=0;

  int      port=-1;
  unsigned pc=0;
  int      dst=-1;

  opterr = 0;

  char opts[32];
  sprintf(opts,"a:C:L:p:hv");

  int c;
  while( (c=getopt(argc,argv,opts))!=-1 ) {
    switch(c) {
    case 'a':
      ip = optarg;
      break;
    case 'p':
      port = strtoul(optarg,NULL,0);
      break;
    case 'C':
      dst = strtoul(optarg,&endptr,0);
      pc  = strtoul(endptr+1,&endptr,0);
      break;
    case 'L':
      latch_tag = strtoul(optarg,NULL,0);
      break;
    case 'v':
      verbose = true;
      break;
    case 'h':
      usage(argv[0]); return 1;
    default:
      break;
    }
  }

  if (verbose)
    printf("port %d dst %d pc %d\n",port,dst,pc);

  Pds::Cphw::Reg::set(ip, 8192, 0);

  MpsSim* p = new ((void*)0x82000000) MpsSim;

  if (port>=0) {
    struct sockaddr_in address;
   
    int s = socket(AF_INET, SOCK_STREAM, 0);
               
    if (s < 0) {
      perror("socket");
      return 0;
    }

    int i = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &i, sizeof i);

    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);
    address.sin_family = AF_INET;
  
    if (bind(s, (struct sockaddr*) &address, sizeof(address)) < 0) {
      perror("bind");
      return 0;
    }

    if (listen(s, 5) < 0) {
      perror("listen");
      return 0;
    }
    
    while(1) {
      int fd;
      socklen_t nsize = sizeof(address);
    
      fd = accept(s, (struct sockaddr*) &address, &nsize);
    
      printf("connection accepted - fd %d\n", fd);
  
      printf("setting TCP_NODELAY to 1\n");
      int flag = 1;
      int optResult = setsockopt(fd,
                                 IPPROTO_TCP,
                                 TCP_NODELAY,
                                 (char *)&flag,
                                 sizeof(int));
      if (optResult < 0)
        perror("TCP_NODELAY error");

      while(p->handle_data(fd)==0);

      if (verbose)
        printf("connection closed - fd %d\n", fd);
      close(fd);
    }
  }
  else {
    p->process(dst,pc,latch_tag);

    unsigned latch, tag, timestamp;
    unsigned pclass[16];
    
    latch     = p->latchDiag();
    tag       = p->tag();
    timestamp = p->timestamp();

    for(unsigned i=0; i<16; i++)
      pclass[i] = p->pclass(i);

    printf("Latch [%u]  Tag [%x]  Timestamp[%x]\n",
           latch, tag, timestamp );
    for(unsigned i=0; i<16; i++)
      printf("  c%u[%x]", i, pclass[i]);
    printf("\n");
    p->dump();
  }

  return 0;
}
