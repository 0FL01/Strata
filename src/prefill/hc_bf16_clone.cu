// Standalone TU: compile with component std17 O2 no-fast-math gfx906 flags.
#include "hc_bf16_clone_gate.hpp"
#include "hc_bf16_clone_kernel.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
namespace strata::prefill::hc_bf16_clone {
thread_local Token* active=nullptr;
[[noreturn]] void fatal(const char* why){
 std::fprintf(stderr,"STRATA_HC_BF16_CLONE_FATAL %s\n",why);std::abort();
}
bool qualify(int device){
 if(!runtime_enabled(std::getenv("STRATA_HC_BF16_CLONE")))return false;
 int current=-1;
 if(hipGetDevice(&current)!=hipSuccess||current!=device)fatal("init device mismatch");
 hipDeviceProp_t p{};
 if(hipGetDeviceProperties(&p,device)!=hipSuccess)fatal("device properties");
 if(std::strncmp(p.gcnArchName,"gfx906",6)||!(p.gcnArchName[6]==0||p.gcnArchName[6]==':')||p.warpSize!=64)
  return false;
 std::fprintf(stderr,"STRATA_HC_BF16_CLONE_INIT_V1 device=%d enabled=1 arch=%s\n",device,p.gcnArchName);
 return true;
}
bool dispatch(const uint16_t* X,const uint16_t* W,float* Y,void* stream,
 int64_t T,int64_t N,int64_t K,int64_t ldy,float beta,int64_t ldx,bool xf16,bool f16io){
 Token* h=active;
 if(!h||!matches(*h,X,W,Y,stream,T,N,K,ldy,beta,ldx,xf16,f16io))return false;
 int current=-1;
 if(hipGetDevice(&current)!=hipSuccess||current!=h->device)fatal("dispatch device mismatch");
 if(hc_lds::launch(false,W,X,Y,int(N),int(T),int(K),static_cast<hipStream_t>(stream))!=hipSuccess)
  fatal("kernel launch");
 h->used=true;++h->counts[h->role];return true;
}
}
