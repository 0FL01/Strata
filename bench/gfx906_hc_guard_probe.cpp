#include <hip/hip_runtime.h>
#include <hip/hip_fp16.h>
#include "strata/prefill/gemm.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
#define CK(c) do { auto e=(c); if(e!=hipSuccess){std::fprintf(stderr,"%s: %s\n",#c,hipGetErrorString(e));std::exit(2);} }while(0)
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);
 hipStream_t st; CK(hipStreamCreate(&st)); bool ok=true;
 const int shapes[][4]={{1,4095,320,10240},{1,4095,10240,320},{1,4096,320,10240},{1,4096,10240,320}};
 for(auto &s:shapes){
  const bool bf=s[0];const int T=s[1],N=s[2],K=s[3];
  std::mt19937 rng(20261007+T+N+K);std::uniform_real_distribution<float>d(-.25f,.25f);
  std::vector<uint16_t>x((size_t)T*K),w((size_t)N*K);
  std::vector<float> xf(x.size()),wf(w.size());
  auto fill=[&](auto& a,auto& f){for(size_t i=0;i<a.size();++i){float v=d(rng);if(bf){uint32_t b;std::memcpy(&b,&v,4);a[i]=b>>16;b=(uint32_t)a[i]<<16;std::memcpy(&f[i],&b,4);}else{__half h=__float2half_rn(v);std::memcpy(&a[i],&h,2);f[i]=__half2float(h);}}};
  fill(x,xf);fill(w,wf);
  const char* mode=std::getenv("STRATA_HC_GUARD_CASE");
  const int test=mode?std::atoi(mode):0;
  auto constant=[](auto& a,auto& f,float v){uint32_t bits;std::memcpy(&bits,&v,4);std::fill(a.begin(),a.end(),uint16_t(bits>>16));std::fill(f.begin(),f.end(),v);};
  if(test==1){constant(x,xf,128.0f);constant(w,wf,.125f);}
  if(test==2){constant(x,xf,.125f);constant(w,wf,16.0f);}
  if(test==3){constant(x,xf,127.5f);constant(w,wf,.125f);}
  if(test==4){constant(x,xf,.125f);constant(w,wf,std::ldexp(1.0f,-40));}
  if(test==5){constant(x,xf,std::ldexp(1.0f,-45));constant(w,wf,.125f);}
  if(test==6){constant(x,xf,-0.0f);constant(w,wf,.125f);}
  uint16_t *dx,*dw;float*dy;void* phase=nullptr;
  CK(hipMalloc((void**)&dx,x.size()*2));CK(hipMalloc((void**)&dw,w.size()*2));CK(hipMalloc((void**)&dy,(size_t)T*N*4));
  CK(hipMemcpy(dx,x.data(),x.size()*2,hipMemcpyHostToDevice));CK(hipMemcpy(dw,w.data(),w.size()*2,hipMemcpyHostToDevice));
  CK(hipMalloc(&phase,160ull<<20));
  double ms=0,rel=0,mx=0;
  {
   strata::prefill::Gemm g;std::string err;if(!g.init(st,32ll<<20,err)){std::fprintf(stderr,"%s\n",err.c_str());return 2;}
   g.set_hc_scratch(phase,160ull<<20);
   auto call=[&](){if(bf)g.bf16(dx,dw,dy,T,N,K);else g.f16(dx,dw,dy,T,N,K);};
   const auto start=std::chrono::steady_clock::now(); call(); CK(hipStreamSynchronize(st));
   const double first_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
   for(int i=0;i<1;++i)call();CK(hipStreamSynchronize(st));
   hipEvent_t a,b;CK(hipEventCreate(&a));CK(hipEventCreate(&b));std::vector<float> times;
   for(int r=0;r<1;++r){CK(hipEventRecord(a,st));for(int i=0;i<1;++i)call();CK(hipEventRecord(b,st));CK(hipEventSynchronize(b));float t;CK(hipEventElapsedTime(&t,a,b));times.push_back(t);}
   std::sort(times.begin(),times.end());ms=times[0];
   std::printf("FIRST bf16=%d T=%d N=%d K=%d wall_ms=%.6f\n",int(bf),T,N,K,first_ms);
   std::vector<float> y((size_t)T*N);CK(hipMemcpy(y.data(),dy,y.size()*4,hipMemcpyDeviceToHost));
   uint64_t hash=1469598103934665603ull;
   for(float v:y){uint32_t u;std::memcpy(&u,&v,4);hash^=u;hash*=1099511628211ull;}
   std::printf("GUARD_CASE %d T=%d N=%d K=%d output_hash=%016llx\n",test,T,N,K,(unsigned long long)hash);
   g.set_hc_scratch(nullptr,0); // Force the unchanged native BF16 route on identical operands.
   g.bf16(dx,dw,dy,T,N,K);CK(hipStreamSynchronize(st));
   std::vector<float> native(y.size());CK(hipMemcpy(native.data(),dy,native.size()*4,hipMemcpyDeviceToHost));
   const bool native_equal=std::memcmp(y.data(),native.data(),y.size()*4)==0;
   if(test!=0 || std::getenv("STRATA_HC_F16_EXACT_INPUT"))ok=ok&&native_equal;
   double ne2=0,nr2=0;
   for(size_t j=0;j<y.size();++j){double z=double(y[j])-native[j];ne2+=z*z;nr2+=double(native[j])*native[j];}
   std::printf("NATIVE_PARITY case=%d T=%d N=%d K=%d bitwise=%d rel_l2=%.9g\n",test,T,N,K,int(native_equal),std::sqrt(ne2/std::max(nr2,1e-300)));
   double d2=0,r2=0;
   for(int i=0;i<64;++i){int t=(i*7919)%T,n=(i*97)%N;double ref=0;for(int k=0;k<K;++k)ref+=(double)xf[(size_t)t*K+k]*wf[(size_t)n*K+k];double dd=y[(size_t)t*N+n]-ref;d2+=dd*dd;r2+=ref*ref;mx=std::max(mx,std::abs(dd));}
   rel=std::sqrt(d2/std::max(r2,1e-300));bool finite=std::all_of(y.begin(),y.end(),[](float v){return std::isfinite(v);});ok=ok&&finite&&rel<1e-4&&mx<5e-3;
   std::printf("{\"bf16\":%s,\"T\":%d,\"N\":%d,\"K\":%d,\"ms\":%.6f,\"rel_l2_sample\":%.9g,\"max_abs_sample\":%.9g,\"all_finite\":%s}\n",bf?"true":"false",T,N,K,ms,rel,mx,finite?"true":"false");
   CK(hipEventDestroy(a));CK(hipEventDestroy(b));
  }
  CK(hipFree(dx));CK(hipFree(dw));CK(hipFree(dy));CK(hipFree(phase));
 }
 CK(hipStreamDestroy(st));return ok?0:1;
}
