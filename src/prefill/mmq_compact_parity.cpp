// Isolated exact-byte parity and paired timing for the opt-in gfx906 Q2_0/J48 scheduler.
#include "strata/prefill/moe_mmq.hpp"
#include "ggml.h"
#include <cuda_runtime.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
#include <chrono>
#include <numeric>
namespace mmq=strata::prefill::mmq;
static void ck(cudaError_t e,const char* what){if(e!=cudaSuccess){std::fprintf(stderr,"%s: %s\n",what,cudaGetErrorString(e));std::exit(2);}}
template<class T> static T* alloc(size_t n){T* p=nullptr;ck(cudaMalloc(&p,n*sizeof(T)),"alloc");return p;}
static float median(std::vector<float> v){std::sort(v.begin(),v.end());return v[v.size()/2];}
int main(int argc,char** argv){
    const int device=argc>1?std::atoi(argv[1]):0;ck(cudaSetDevice(device),"device");
    setenv("STRATA_GFX906_PREFILL_J48","1",1);
    std::mt19937 rng(7);
    const char* names[]={"balanced96","skew600","longskew2048","zeros96","tails145"};
    for(int shape=0;shape<2;++shape)for(int cs=0;cs<5;++cs){
        const int out=shape?2560:1280,in=shape?640:2560,E=16;
        int counts[E];std::fill(counts,counts+E,96);
        if(cs==1){std::fill(counts,counts+E,80);counts[0]=600;}
        if(cs==2){std::fill(counts,counts+E,40);counts[0]=2048;}
        if(cs==3){std::fill(counts,counts+E,0);counts[0]=96;}
        if(cs==4){for(int e=0;e<E;++e)counts[e]=e*9+1;counts[0]=145;}
        const int start=(!shape && (cs&1))?17:0;
        std::vector<int32_t> bounds(E+1,start);for(int e=0;e<E;++e)bounds[e+1]=bounds[e]+counts[e];
        const int T=bounds[E],maxr=*std::max_element(counts,counts+E);
        const size_t per=mmq::matrix_bytes(GGML_TYPE_Q2_0,out,in),bs=ggml_type_size(GGML_TYPE_Q2_0);
        std::vector<uint8_t> w(E*per+4096,0);
        for(size_t i=0;i<E*per;++i)w[i]=(uint8_t)rng();
        for(size_t i=0;i<E*per;i+=bs){uint16_t d=0x2000+(rng()%256);std::memcpy(w.data()+i,&d,2);}
        std::vector<float> x((size_t)T*in);
        for(auto& v:x)v=((int)(rng()%20001)-10000)*0.001f;
        auto* dw=alloc<uint8_t>(w.size());auto* dx=alloc<float>(x.size());
        auto* dq=alloc<uint8_t>(mmq::q8_bytes(T,in));auto* db=alloc<int32_t>(E+1);auto* ids=alloc<int32_t>(T+128);
        const size_t words=(size_t)T*out;
        auto* ref=alloc<float>(words+128);auto* got=alloc<float>(words+128);
        ck(cudaMemcpy(dw,w.data(),w.size(),cudaMemcpyHostToDevice),"weights");
        ck(cudaMemcpy(dx,x.data(),x.size()*4,cudaMemcpyHostToDevice),"activation");
        ck(cudaMemcpy(db,bounds.data(),bounds.size()*4,cudaMemcpyHostToDevice),"bounds");
        std::vector<int32_t> hids(T+128);std::iota(hids.begin(),hids.end(),0);
        std::shuffle(hids.begin()+start,hids.begin()+T,rng);
        ck(cudaMemcpy(ids,hids.data(),hids.size()*4,cudaMemcpyHostToDevice),"ids permutation");
        mmq::quantize(dx,nullptr,dq,GGML_TYPE_Q2_0,in,in,T,nullptr);
        mmq::Context ctx;mmq::Product p;
        p.w=dw;p.type=GGML_TYPE_Q2_0;p.w_rows=out;p.w_cols=in;p.expert_bytes=per;p.n=E;
        p.xq=dq;p.bounds=db;p.ids=ids;p.total_rows=T;p.max_rows=maxr;p.ld_dst=out;
        p.local_full_routing_prefill=true;p.host_counts_valid=true;
        std::copy(counts,counts+E,p.host_counts);
        bool taken=false;p.compact_taken=&taken;
        ck(cudaMemset(ref,0xA5,(words+128)*4),"poison ref");ck(cudaMemset(got,0xA5,(words+128)*4),"poison got");
        p.dst=ref;p.compact_tiles=false;ctx.run(p,nullptr);if(taken)return 3;
        p.dst=got;p.compact_tiles=true;ctx.run(p,nullptr);if(!taken){std::fprintf(stderr,"candidate fallback %s shape%d\n",names[cs],shape);return 4;}
        ck(cudaDeviceSynchronize(),"parity");
        std::vector<uint32_t> hr(words+128),hg(words+128);
        ck(cudaMemcpy(hr.data(),ref,hr.size()*4,cudaMemcpyDeviceToHost),"ref read");
        ck(cudaMemcpy(hg.data(),got,hg.size()*4,cudaMemcpyDeviceToHost),"got read");
        size_t mismatch=0;while(mismatch<hr.size()&&hr[mismatch]==hg[mismatch])++mismatch;
        if(mismatch<hr.size()){std::fprintf(stderr,"FAIL %s shape%d word%zu %08x %08x\n",names[cs],shape,mismatch,hr[mismatch],hg[mismatch]);return 5;}
        for(size_t i=0;i<(size_t)start*out;++i)if(hr[i]!=0xA5A5A5A5u)return 8;
        for(size_t i=words;i<words+128;++i)if(hr[i]!=0xA5A5A5A5u)return 6;
        cudaEvent_t a,b;ck(cudaEventCreate(&a),"event");ck(cudaEventCreate(&b),"event");
        std::vector<float> base,cand,wall_base,wall_cand;
        for(int repeat=0;repeat<45;++repeat)for(int arm_i=0;arm_i<2;++arm_i){
            const int arm=(repeat&1)?1-arm_i:arm_i;
            p.dst=arm?got:ref;p.compact_tiles=arm;
            const auto wall_start=std::chrono::steady_clock::now();
            ck(cudaEventRecord(a),"record");ctx.run(p,nullptr);ck(cudaEventRecord(b),"record");ck(cudaEventSynchronize(b),"wait");
            if(taken!=(bool)arm)return 7;
            float ms=0;ck(cudaEventElapsedTime(&ms,a,b),"elapsed");if(repeat>=5){(arm?cand:base).push_back(ms);(arm?wall_cand:wall_base).push_back(std::chrono::duration<float,std::milli>(std::chrono::steady_clock::now()-wall_start).count());}
        }
        std::printf("COMPACT_PARITY case=%s shape=%d rows=%d max=%d words=%zu equal=1 baseline_ms=%.6f compact_ms=%.6f ratio=%.6f\n",
            names[cs],shape,T,maxr,words,median(base),median(cand),median(cand)/median(base));std::fflush(stdout);
        std::printf("COMPACT_SAMPLES device=%d case=%s shape=%d wall_base_ms=%.6f wall_compact_ms=%.6f\n",device,names[cs],shape,median(wall_base),median(wall_cand));
        for(size_t i=0;i<base.size();++i)std::printf("PAIR %zu %.9f %.9f %.9f %.9f\n",i,base[i],cand[i],wall_base[i],wall_cand[i]);
        cudaEventDestroy(a);cudaEventDestroy(b);cudaFree(dw);cudaFree(dx);cudaFree(dq);cudaFree(db);cudaFree(ids);cudaFree(ref);cudaFree(got);
    }
    return 0;
}
