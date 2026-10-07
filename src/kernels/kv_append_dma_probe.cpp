// Disposable INT8 prompt append versus append+DMA probe. No model or engine dispatch changes.
#include "strata/prefill/kernels.hpp"
#include "strata/kernels/kv_stream.hpp"
#include <cuda_runtime.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
namespace k=strata::kernels;
static void ck(cudaError_t e){if(e!=cudaSuccess){std::fprintf(stderr,"%s\n",cudaGetErrorString(e));std::exit(2);}}
struct Buffer {
 void* p=nullptr; void* host=nullptr;size_t bytes;
 Buffer(size_t n,bool h):bytes(n){
  if(h){ck(cudaHostAlloc(&host,n+64,cudaHostAllocMapped));std::memset(host,0x31,n+64);ck(cudaHostGetDevicePointer(&p,host,0));}
  else{ck(cudaMalloc(&p,n+64));ck(cudaMemset(p,0xa5,n+64));}
 }
 ~Buffer(){if(host)cudaFreeHost(host);else cudaFree(p);}
 std::vector<uint8_t> read(){std::vector<uint8_t> v(bytes+64);if(host)std::memcpy(v.data(),host,v.size());else ck(cudaMemcpy(v.data(),p,v.size(),cudaMemcpyDeviceToHost));return v;}
};
struct Pool{
 Buffer kq,vq,ks,vs;
 Pool(int cells,bool h):kq(size_t(cells)*512,h),vq(size_t(cells)*512,h),ks(size_t(cells)*16,h),vs(size_t(cells)*16,h){}
 k::KvHostPools ptr(){k::KvHostPools r;r.k_q=(int8_t*)kq.p;r.v_q=(int8_t*)vq.p;r.k_scale=(uint16_t*)ks.p;r.v_scale=(uint16_t*)vs.p;return r;}
 k::QsaAttnPools attn(){auto p=ptr();k::QsaAttnPools a;a.k_q=p.k_q;a.v_q=p.v_q;a.k_scale=p.k_scale;a.v_scale=p.v_scale;return a;}
 std::vector<std::vector<uint8_t>> read(){return {kq.read(),vq.read(),ks.read(),vs.read()};}
};
int main(){
 k::QsaShapes s;s.n_head_kv=2;s.head_dim=256;s.page_size=4;
 cudaStream_t st;ck(cudaStreamCreateWithFlags(&st,cudaStreamNonBlocking));
 std::mt19937 rng(1519);std::normal_distribution<float> normal(0,.7f);
 int cases=0,bad=0;
 for(int p0:{0,3,32767,32768})for(int T:{1,4095,4096}){
  int end=p0+T,pages=(end+3)/4,cells=pages*4,slots=(pages+2)/3;
  std::vector<int32_t> table(pages,-1);for(int b=0;b<pages;b+=3)table[b]=b/3;
  Buffer dt(table.size()*4,false);ck(cudaMemcpy(dt.p,table.data(),table.size()*4,cudaMemcpyHostToDevice));
  std::vector<float> K(size_t(T)*512),V(K.size());for(auto&v:K)v=normal(rng);for(auto&v:V)v=normal(rng);
  Buffer dk(K.size()*4,false),dv(V.size()*4,false);
  ck(cudaMemcpy(dk.p,K.data(),K.size()*4,cudaMemcpyHostToDevice));ck(cudaMemcpy(dv.p,V.data(),V.size()*4,cudaMemcpyHostToDevice));
  Pool ha(cells,true),hb(cells,true),sa(cells,false),sb(cells,false),ra(slots*4,false),rb(slots*4,false);
  auto hap=ha.ptr(),hbp=hb.ptr(),sap=sa.ptr(),sbp=sb.ptr(),rap=ra.ptr(),rbp=rb.ptr();
  // The engine stages the existing prefix, including a partial first append page.
  k::kv_stage_from_host(sa.attn(),hap,k::kKvInt8,(p0+3)/4,s,st);
  k::kv_stage_from_host(sb.attn(),hbp,k::kKvInt8,(p0+3)/4,s,st);
  auto run=[&](bool dma){
   auto resident=dma?rbp:rap;auto stage=dma?sbp:sap;
   strata::prefill::kv_append((float*)dk.p,(float*)dv.p,T,p0,(int32_t*)dt.p,4,nullptr,nullptr,
    resident.k_q,resident.v_q,resident.k_scale,resident.v_scale,st,dma?nullptr:&hap,&stage);
   if(dma)k::kv_unstage_to_host(sb.attn(),hbp,k::kKvInt8,p0/4,(end+3)/4,s,st);
  };
  run(false);run(true);ck(cudaStreamSynchronize(st));
  auto a=ha.read(),b=hb.read();bool same=true;
  // Compare all initialized prefix and appended cells, excluding unconsumed future tail.
  for(int f=0;f<4;++f){int width=f<2?256:8;
   for(int pos=0;pos<end;++pos)for(int head=0;head<2;++head){
    size_t off=(size_t(pos/4)*8+head*4+pos%4)*width;
    same &= std::memcmp(a[f].data()+off,b[f].data()+off,width)==0;
   }
   for(size_t i=a[f].size()-64;i<a[f].size();++i)same &= a[f][i]==0x31&&b[f][i]==0x31;
  }
  same &= sa.read()==sb.read();same &= ra.read()==rb.read();
  if(!same)++bad;++cases;
  std::printf("PARITY p0=%d T=%d %s\n",p0,T,same?"pass":"FAIL");
  if(T==4096){
   cudaEvent_t e0,e1;ck(cudaEventCreate(&e0));ck(cudaEventCreate(&e1));
   std::vector<float> times[2];
   for(int rep=0;rep<11;++rep)for(int j=0;j<2;++j){
    int arm=(rep%2)?1-j:j;
    ck(cudaEventRecord(e0,st));run(arm);ck(cudaEventRecord(e1,st));ck(cudaEventSynchronize(e1));
    float ms=0;ck(cudaEventElapsedTime(&ms,e0,e1));if(rep>=3)times[arm].push_back(ms);
   }
   for(auto&v:times)std::sort(v.begin(),v.end());
   float x=times[0][times[0].size()/2],y=times[1][times[1].size()/2];
   std::printf("BENCH p0=%d T=%d direct_ms=%.6f dma_ms=%.6f speedup=%.6f\n",p0,T,x,y,x/y);
   ck(cudaEventDestroy(e0));ck(cudaEventDestroy(e1));
  }
  std::fflush(stdout);
 }
 ck(cudaStreamDestroy(st));std::printf("kv append DMA: %d cases %d failures\n",cases,bad);return bad?1:0;
}
