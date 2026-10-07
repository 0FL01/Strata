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
 const int shapes[][4]={{1,4095,320,10240},{1,4095,10240,320},{1,4096,320,10240},{1,4096,10240,320},{1,1535,320,10240},{1,1535,10240,320},{1,1536,320,10240},{1,1536,10240,320},{1,3071,320,10240},{1,3071,10240,320},{1,3072,320,10240},{1,3072,10240,320},{1,256,320,10240},{0,4096,12288,2560},{0,64,1280,2560},{0,256,1280,2560},{0,128,2560,640}};
 for(auto &s:shapes){
  const bool bf=s[0];const int T=s[1],N=s[2],K=s[3];
  std::mt19937 rng(20261007+T+N+K);std::uniform_real_distribution<float>d(-.25f,.25f);
  std::vector<uint16_t>x((size_t)T*K),w((size_t)N*K);
  std::vector<float> xf(x.size()),wf(w.size());
  auto fill=[&](auto& a,auto& f){for(size_t i=0;i<a.size();++i){float v=d(rng);if(bf){uint32_t b;std::memcpy(&b,&v,4);a[i]=b>>16;b=(uint32_t)a[i]<<16;std::memcpy(&f[i],&b,4);}else{__half h=__float2half_rn(v);std::memcpy(&a[i],&h,2);f[i]=__half2float(h);}}};
  fill(x,xf);fill(w,wf);uint16_t *dx,*dw;float*dy;void* phase=nullptr;
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
   for(int i=0;i<2;++i)call();CK(hipStreamSynchronize(st));
   hipEvent_t a,b;CK(hipEventCreate(&a));CK(hipEventCreate(&b));std::vector<float> times;
   for(int r=0;r<5;++r){CK(hipEventRecord(a,st));for(int i=0;i<10;++i)call();CK(hipEventRecord(b,st));CK(hipEventSynchronize(b));float t;CK(hipEventElapsedTime(&t,a,b));times.push_back(t/10);}
   std::sort(times.begin(),times.end());ms=times[2];
   std::printf("FIRST bf16=%d T=%d N=%d K=%d wall_ms=%.6f\n",int(bf),T,N,K,first_ms);
   std::vector<float> y((size_t)T*N);CK(hipMemcpy(y.data(),dy,y.size()*4,hipMemcpyDeviceToHost));
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
