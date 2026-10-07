#include "strata/kernels/cpu/expert.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
namespace c = strata::kernels::cpu;
static bool pair_test = false;
using Clock=std::chrono::steady_clock;
static void ref(const uint8_t* w,size_t rb,int nb,const c::ActQ* const* a,int nt,float* const* o,int r0,int r1){
 if(pair_test)c::q2_0_gguf_rows_multi_avx2_spread(w,rb,nb,a,nt,o,r0,r1);
 else c::q2_0_gguf_rows_multi_avx2_v(false,w,rb,nb,a,nt,o,r0,r1);
}
static void alt(const uint8_t* w,size_t rb,int nb,const c::ActQ* const* a,int nt,float* const* o,int r0,int r1){
 if(pair_test)c::q2_0_gguf_rows_multi_avx2_pair(w,rb,nb,a,nt,o,r0,r1);
 else c::q2_0_gguf_rows_multi_avx2_spread(w,rb,nb,a,nt,o,r0,r1);
}
static void weights(std::vector<uint8_t>& w,int rows,int nb,size_t rb,std::mt19937& rng){
 for(auto&v:w)v=uint8_t(rng());
 for(int r=0;r<rows;++r)for(int b=0;b<nb;++b){
  uint16_t h=uint16_t(0x2800+rng()%0x1400);if(rng()&1)h|=0x8000;
  std::memcpy(w.data()+size_t(r)*rb+b*18,&h,2);
 }
}
int main(int argc,char**){
 if(!c::cpu_avx2_ok())return 77;
 pair_test=std::getenv("STRATA_Q2_TEST_PAIR") != nullptr;
 const char* flag=std::getenv("STRATA_Q2_AVX2_SPREAD");
 if(flag&&flag[0]=='1'){std::fprintf(stderr,"unset STRATA_Q2_AVX2_SPREAD for independent reference\n");return 2;}
 size_t checks=0,bad=0;
 c::ActQ a{};a.scale[0]=a.scale[1]=1;a.nchunks=2;
 const c::ActQ* ap[]={&a};float x=0,y=0;float* xp[]={&x};float* yp[]={&y};
 uint8_t w[18]={0,0x3c};
 for(int v=0;v<256;++v)for(int pos=0;pos<16;++pos)for(int sub=0;sub<4;++sub){
  for(int j=0;j<16;++j)w[j+2]=uint8_t(0xa5^(j*17));w[pos+2]=uint8_t(v);
  std::fill(a.q,a.q+64,0);a.hx[0]=a.hx[1]=0;
  int k=pos*4+sub;a.q[k]=1;a.hx[k/32]=1;
  ref(w,18,1,ap,1,xp,0,1);alt(w,18,1,ap,1,yp,0,1);
  const float expected=float(((v>>(2*sub))&3)-1);
  bad+=std::memcmp(&x,&y,4)!=0||y!=expected;++checks;
 }
 std::mt19937 rng(20261007);
 for(int nb:{0,1,3,10,40})for(int nt=1;nt<=8;++nt)for(int pad:{0,13}){
  constexpr int R=65;size_t rb=size_t(nb)*18+pad+1;
  std::vector<uint8_t> ww(size_t(R)*rb);weights(ww,R,nb,rb,rng);
  std::vector<c::ActQ> aa(nt);std::vector<const c::ActQ*> pp(nt);
  std::vector<float> xx(size_t(nt)*R,12345.25f),yy=xx;std::vector<float*> px(nt),py(nt);
  for(int t=0;t<nt;++t){
   std::vector<float> input(std::max(1,nb*64));for(auto&z:input)z=float(int(rng()%20001)-10000)/1024.f;
   if(nb)c::act_quant_q8_1_avx2(input.data(),nb*64,aa[t]);
   pp[t]=&aa[t];px[t]=xx.data()+t*R;py[t]=yy.data()+t*R;
  }
  ref(ww.data(),rb,nb,pp.data(),nt,px.data(),3,R-5);
  alt(ww.data(),rb,nb,pp.data(),nt,py.data(),3,R-5);
  bad+=std::memcmp(xx.data(),yy.data(),xx.size()*4)!=0;++checks;
 }
 std::printf("parity checks=%zu bad=%zu\n",checks,bad);if(bad)return 1;
 if(argc<=1)return 0;
 volatile float sink=0;
 for(int nb:{10,40})for(int nt:{1,2,3,4,5,6,7,8})for(int copies:{1,256}){
  const int rows=nb==10?2560:640;const size_t rb=size_t(nb)*18,bytes=rb*rows;
  std::vector<uint8_t> ww(bytes*copies);weights(ww,rows*copies,nb,rb,rng);
  std::vector<c::ActQ> aa(nt);std::vector<const c::ActQ*> pp(nt);
  std::vector<float> out(size_t(nt)*rows);std::vector<float*> op(nt);
  for(int t=0;t<nt;++t){
   std::vector<float> input(nb*64);for(auto&z:input)z=float(int(rng()%20001)-10000)/1024.f;
   c::act_quant_q8_1_avx2(input.data(),nb*64,aa[t]);pp[t]=&aa[t];op[t]=out.data()+t*rows;
  }
  const int iters=copies==1?100:256;
  auto bench=[&](bool candidate){
   auto fn=candidate?alt:ref;fn(ww.data(),rb,nb,pp.data(),nt,op.data(),0,rows);
   auto start=Clock::now();
   for(int i=0;i<iters;++i)fn(ww.data()+size_t(i%copies)*bytes,rb,nb,pp.data(),nt,op.data(),0,rows);
   sink=out[0];return std::chrono::duration<double,std::micro>(Clock::now()-start).count()/iters;
  };
  double r0=bench(false),s0=bench(true),s1=bench(true),r1=bench(false);
  std::printf("BENCH blocks=%d tokens=%d copies=%d ref_us=%.6f spread_us=%.6f speedup=%.6f\n",
   nb,nt,copies,(r0+r1)/2,(s0+s1)/2,(r0+r1)/(s0+s1));std::fflush(stdout);
 }
 (void)sink;return 0;
}
