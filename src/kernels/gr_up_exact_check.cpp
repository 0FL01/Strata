// Synthetic exact fused HC read check; QFUSE remains outside this candidate's scope.
#include "strata/kernels/fused_gr.hpp"
#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
namespace k = strata::kernels;
static void ck(cudaError_t e) { if(e != cudaSuccess) { std::fprintf(stderr,"%s\n",cudaGetErrorString(e)); std::exit(2); } }
template<class T> T* alloc(size_t n) { T* p=nullptr; ck(cudaMalloc(&p,(n+16)*sizeof(T))); ck(cudaMemset(p,0xa5,(n+16)*sizeof(T))); return p; }
template<class T> T* upload(const std::vector<T>& v) { T* p=alloc<T>(v.size()); ck(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice)); return p; }
static uint16_t bf(float x) { uint32_t u; std::memcpy(&u,&x,4); return u>>16; }
int main() {
 constexpr int N=2560,HC=4,LR=320,D=N*HC;
 std::mt19937 gen(1361); std::normal_distribution<float> normal(0,.2f);
 std::vector<float> norm(D); for(auto&v:norm)v=1+normal(gen);
 std::vector<uint16_t> wd(D*LR),wu(D*LR),wi(D*HC);
 for(auto&v:wd)v=bf(normal(gen)); for(auto&v:wu)v=bf(normal(gen)); for(auto&v:wi)v=bf(normal(gen));
 auto dn=upload(norm); auto dd=upload(wd);auto du=upload(wu);auto di=upload(wi);
 cudaStream_t stream;ck(cudaStreamCreateWithFlags(&stream,cudaStreamNonBlocking));
 int cases=0,bad=0;
 for(int T=1;T<=8;++T) for(int apply=0;apply<2;++apply) for(int inject=0;inject<2;++inject) {
  std::vector<float> r(T*D),bo(T*N),inj(T*HC);
  for(auto&v:r)v=normal(gen);for(auto&v:bo)v=normal(gen);for(auto&v:inj)v=normal(gen);
  auto dr=upload(r);auto db=upload(bo);auto dj=upload(inj);
  auto dout=alloc<float>(T*D);auto lo=alloc<float>(T*LR);auto rs=alloc<float>(T*HC);
  auto io=alloc<float>(T*HC);auto mixed=alloc<float>(T*N);auto xn=alloc<float>(T*D);
  std::vector<k::FusedGrArgs> args(T);
  for(int t=0;t<T;++t) {
   auto&a=args[t];a.R=dr+t*D;a.R_out=dout+t*D;a.apply=apply;
   a.bo_prev=db+t*N;a.inj_prev=dj+t*HC;a.w_norm=dn;a.w_down=dd;a.w_up=du;
   a.w_inject=inject?di:nullptr;a.eps=1e-6f;a.lo=lo+t*LR;a.rs=rs+t*HC;
   a.inject_out=io+t*HC;a.mixed=mixed+t*N;
  }
  std::vector<std::pair<float*,size_t>> outputs={{dout,size_t(T*D)},{lo,size_t(T*LR)},{rs,size_t(T*HC)},{io,size_t(T*HC)},{mixed,size_t(T*N)}};
  auto poison=[&](){for(auto o:outputs)ck(cudaMemsetAsync(o.first,0xa5,(o.second+16)*4,stream));};
  auto snap=[&](){std::vector<std::vector<uint32_t>> out; for(auto o:outputs){out.emplace_back(o.second+16);ck(cudaMemcpy(out.back().data(),o.first,(o.second+16)*4,cudaMemcpyDeviceToHost));}return out;};
  auto reference=[&](){poison();for(auto&a:args)k::fused_gr_read(a,stream);ck(cudaStreamSynchronize(stream));return snap();};
  auto ref=reference();
  poison();k::fused_gr_read_multi(args.data(),T,xn,stream);ck(cudaStreamSynchronize(stream));
  if(snap()!=ref){std::printf("FAIL direct T=%d apply=%d inject=%d\n",T,apply,inject);++bad;}
  cudaGraph_t graph;cudaGraphExec_t exec;
  ck(cudaStreamBeginCapture(stream,cudaStreamCaptureModeThreadLocal));
  k::fused_gr_read_multi(args.data(),T,xn,stream);
  ck(cudaStreamEndCapture(stream,&graph));ck(cudaGraphInstantiate(&exec,graph,nullptr,nullptr,0));
  for(int rep=0;rep<2;++rep){
   for(auto&v:r)v=v*(-.7f)+.013f;
   ck(cudaMemcpyAsync(dr,r.data(),r.size()*4,cudaMemcpyHostToDevice,stream));
   ref=reference();poison();ck(cudaGraphLaunch(exec,stream));ck(cudaStreamSynchronize(stream));
   if(snap()!=ref){std::printf("FAIL graph T=%d apply=%d inject=%d rep=%d\n",T,apply,inject,rep);++bad;}
  }
  if(apply&&inject){
   for(int i=0;i<10;++i)ck(cudaGraphLaunch(exec,stream));
   cudaEvent_t a,b;ck(cudaEventCreate(&a));ck(cudaEventCreate(&b));
   for(int rep=0;rep<5;++rep){
    ck(cudaEventRecord(a,stream));for(int i=0;i<100;++i)ck(cudaGraphLaunch(exec,stream));
    ck(cudaEventRecord(b,stream));ck(cudaEventSynchronize(b));float ms=0;ck(cudaEventElapsedTime(&ms,a,b));
    std::printf("BENCH T=%d rep=%d us=%.6f\n",T,rep,ms*10);
   }
   ck(cudaEventDestroy(a));ck(cudaEventDestroy(b));
  }
  ++cases;ck(cudaGraphExecDestroy(exec));ck(cudaGraphDestroy(graph));
  for(auto o:outputs)ck(cudaFree(o.first));ck(cudaFree(dr));ck(cudaFree(db));ck(cudaFree(dj));ck(cudaFree(xn));
 }
 ck(cudaStreamDestroy(stream));ck(cudaFree(dn));ck(cudaFree(dd));ck(cudaFree(du));ck(cudaFree(di));
 std::printf("fused HC exact-up: %d cases, %d failures\n",cases,bad);return bad?1:0;
}
