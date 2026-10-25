#pragma once
#include <cstdint>
namespace strata::prefill::hc_bf16_clone {
inline bool exact_one(const char* v){return v&&v[0]=='1'&&v[1]==0;}
// Measured gfx906 default; exact0 is the rollback, other explicit values disable.
inline bool runtime_enabled(const char* v){return v==nullptr||exact_one(v);}
inline bool shape(int role,int64_t T,int64_t N,int64_t K){
 return (T==4096||T==4093)&&((role==0&&N==320&&K==10240)||(role==1&&N==10240&&K==320));
}
struct Token {
 int role,device;int64_t T,N,K;void* stream;
 const uint16_t* X;const uint16_t* W;float* Y;
 uint64_t* counts;bool used=false;
};
extern thread_local Token* active;
[[noreturn]] void fatal(const char*);
bool qualify(int device);
struct Scope {
 Token value;Token* previous;bool on;
 Scope(bool enabled,int role,int device,int64_t T,int64_t N,int64_t K,void* stream,
       const uint16_t* X,const uint16_t* W,float* Y,uint64_t* counts):
  value{role,device,T,N,K,stream,X,W,Y,counts,false},previous(active),on(enabled){
  if(on){if(previous)fatal("nested role");active=&value;}
 }
 ~Scope(){if(on)active=previous;}
 Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
};
inline bool matches(const Token& h,const uint16_t* X,const uint16_t* W,float* Y,
 void* stream,int64_t T,int64_t N,int64_t K,int64_t ldy,float beta,int64_t ldx,bool xf16,bool f16io){
 return !h.used&&h.counts&&X&&W&&Y&&h.X==X&&h.W==W&&h.Y==Y&&h.stream==stream&&
  h.T==T&&h.N==N&&h.K==K&&shape(h.role,T,N,K)&&ldy==N&&ldx==0&&beta==0.0f&&!xf16&&!f16io;
}
bool dispatch(const uint16_t* X,const uint16_t* W,float* Y,void* stream,
 int64_t T,int64_t N,int64_t K,int64_t ldy,float beta,int64_t ldx,bool xf16,bool f16io);
} // namespace
