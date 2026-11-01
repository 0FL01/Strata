// Source-only additive MTP indexed-head component benchmark.
// Derived helpers: retained topk_tail_component_bench (ELF/graph/dump),
// qsa_rows_component_bench (paired Timer), b6_mmvq_bench/mmvq_multi_parity (shared Q8).
#include "strata/kernels/native_mmvq.hpp"
#include "strata/kernels/verify_kernels.hpp"
#include "fixture-pins.hpp"
#include <cuda_runtime.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <elf.h>
#include <functional>
#include <stdexcept>
#include <string>
#include <sys/stat.h>
#include <vector>
namespace k=strata::kernels;
namespace {
constexpr int NI=2560, NS=248320, NO=58963, ROW=1760, G=128, CASES=8;
constexpr size_t WB=size_t(NS)*ROW, CB=size_t(NO)*ROW, XB=NI*4, QB=NI/32*36, MB=NO*4, YB=NO*4;
constexpr uint64_t DUMP_BYTES=64+CASES*(64+XB+QB+MB+2*YB+5*2*G);
constexpr uint32_t SENT=0x7f7f7f7f;
const char* BASE_OBJECT="_ZN6strata7kernels12_GLOBAL__N_123native_mmvq_wave_kernelINS1_9Q5KTraitsELi1ELi2EEEvPKNT_5BlockEPKNS1_8Q81BlockEPfii";
const char* BASE_FUNC="_ZN6strata7kernels12_GLOBAL__N_138__device_stub__native_mmvq_wave_kernelINS1_9Q5KTraitsELi1ELi2EEEvPKNT_5BlockEPKNS1_8Q81BlockEPfii";
const char* INDEX_OBJECT="_ZN6strata7kernels12_GLOBAL__N_140native_q5_k_mtp_head_indexed_wave_kernelINS1_9Q5KTraitsELi1ELi2EEEvPKNT_5BlockEPKNS1_8Q81BlockEPfPKiii";
const char* INDEX_FUNC="_ZN6strata7kernels12_GLOBAL__N_155__device_stub__native_q5_k_mtp_head_indexed_wave_kernelINS1_9Q5KTraitsELi1ELi2EEEvPKNT_5BlockEPKNS1_8Q81BlockEPfPKiii";
cudaStream_t stream=nullptr;
bool base_r2=false;
[[noreturn]] void fail(const char* why){std::fprintf(stderr,"ERROR %s\n",why);std::exit(2);}
void ck(cudaError_t e,const char* op){if(e!=cudaSuccess){std::fprintf(stderr,"ERROR op=%s detail=%s\n",op,cudaGetErrorString(e));std::exit(2);}}
const char* env(const char*n){const char*v=std::getenv(n);return v?v:"UNSET";}
uint64_t hash(const void*p,size_t n){uint64_t h=14695981039346656037ull;auto b=(const unsigned char*)p;for(size_t i=0;i<n;++i){h^=b[i];h*=1099511628211ull;}return h;}
template<class T>uint64_t hash(const std::vector<T>&v){return hash(v.data(),v.size()*sizeof(T));}
float asfloat(uint32_t u){float x;std::memcpy(&x,&u,4);return x;}
uint32_t bits(float x){uint32_t u;std::memcpy(&u,&x,4);return u;}
struct Guard {
    unsigned char*raw=nullptr;size_t n;unsigned char guard;
    Guard(size_t bytes,unsigned char canary):n(bytes),guard(canary){ck(cudaMalloc((void**)&raw,n+2*G),"alloc");ck(cudaMemset(raw,guard,n+2*G),"init_guard");}
    unsigned char* data()const{return raw+G;}
    void put(const void*p){ck(cudaMemcpy(data(),p,n,cudaMemcpyHostToDevice),"upload");}
    std::vector<unsigned char> get()const{std::vector<unsigned char>x(n+2*G);ck(cudaMemcpy(x.data(),raw,x.size(),cudaMemcpyDeviceToHost),"download");return x;}
    bool guards()const{unsigned char a[G],b[G];ck(cudaMemcpy(a,raw,G,cudaMemcpyDeviceToHost),"guard_prefix");ck(cudaMemcpy(b,data()+n,G,cudaMemcpyDeviceToHost),"guard_suffix");for(int i=0;i<G;++i)if(a[i]!=guard||b[i]!=guard)return false;return true;}
    void reset(){ck(cudaMemsetAsync(raw,guard,n+2*G,stream),"reset_outside_events");}
    ~Guard(){ck(cudaFree(raw),"free");}
};
bool stat_matches(const struct stat&s,bool gguf){
    uint64_t mt=uint64_t(s.st_mtim.tv_sec)*1000000000ull+uint64_t(s.st_mtim.tv_nsec);
    uint64_t ct=uint64_t(s.st_ctim.tv_sec)*1000000000ull+uint64_t(s.st_ctim.tv_nsec);
    return uint64_t(s.st_dev)==(gguf?PIN_GGUF_DEV:PIN_VOCAB_DEV)&&
      uint64_t(s.st_ino)==(gguf?PIN_GGUF_INO:PIN_VOCAB_INO)&&
      uint64_t(s.st_size)==(gguf?PIN_GGUF_SIZE:PIN_VOCAB_SIZE)&&
      mt==(gguf?PIN_GGUF_MTIME_NS:PIN_VOCAB_MTIME_NS)&&ct==(gguf?PIN_GGUF_CTIME_NS:PIN_VOCAB_CTIME_NS);
}
std::vector<unsigned char> read_fixture(const std::string&path,bool gguf){
    FILE*f=std::fopen(path.c_str(),"rb");if(!f)fail("fixture_open");
    struct stat s{};if(fstat(fileno(f),&s)||!stat_matches(s,gguf))fail("fixture_stat_before");
    size_t n=gguf?WB:MB;std::vector<unsigned char>b(n);
    if(gguf&&fseeko(f,off_t(PIN_HEAD_OFFSET),SEEK_SET))fail("fixture_seek");
    if(std::fread(b.data(),1,n,f)!=n)fail("fixture_short_read");
    if(fstat(fileno(f),&s)||!stat_matches(s,gguf))fail("fixture_stat_after");
    if(std::fclose(f))fail("fixture_close");return b;
}
struct Files {
    FILE*dump=nullptr,*timing=nullptr;uint64_t bytes=0;int records=0;
    Files(const std::string&p){
        dump=std::fopen(p.c_str(),"wb");timing=std::fopen((p+".timings.csv").c_str(),"w");
        if(!dump||!timing)fail("open_output");
        write("MTPIDX01",8);for(uint64_t x:{uint64_t(CASES),uint64_t(NI),uint64_t(NS),uint64_t(NO),uint64_t(G),uint64_t(QB),uint64_t(SENT)})u64(x);
        std::fprintf(timing,"metric,pair,order,A_us,B_us\n");
    }
    void write(const void*p,size_t n){if(std::fwrite(p,1,n,dump)!=n)fail("dump_write");bytes+=n;}
    void u64(uint64_t n){write(&n,8);}
    void record(int phase,int pattern,const std::vector<unsigned char>&x,const std::vector<unsigned char>&q,
                const std::vector<unsigned char>&m,const std::vector<unsigned char>&a,const std::vector<unsigned char>&b){
        for(uint64_t n:{uint64_t(records),uint64_t(phase),uint64_t(pattern),hash(x),hash(q),hash(m),hash(a),hash(b)})u64(n);
        for(const auto*v:{&x,&q,&m,&a,&b})write(v->data(),v->size());++records;
    }
    void close(){if(records!=CASES||bytes!=DUMP_BYTES)fail("dump_framing");if(std::ferror(timing))fail("timing_write");if(std::fclose(dump)||std::fclose(timing))fail("output_close");}
};
struct Fixture {
    std::vector<unsigned char> whost,mhost,xexpected,qexpected,mexpected,reference0,saved_x0,saved_q0;
    std::vector<int32_t> ids;
    Guard w{WB,0xa5}, compact{CB,0xa5}, xf{XB,0xa5},q{QB,0xa5},map{MB,0},a{YB,0x7f},b{YB,0x7f};
    int pattern=0;
    Fixture(std::vector<unsigned char>weights,std::vector<unsigned char>mapping):whost(std::move(weights)),mhost(std::move(mapping)),ids(NO){
        std::memcpy(ids.data(),mhost.data(),MB);
        std::vector<unsigned char>seen(NS,0);int descending=0;
        for(int i=0;i<NO;++i){int id=ids[i];if(id<0||id>=NS||seen[id])fail("map_range_or_duplicate");seen[id]=1;if(i&&ids[i]<ids[i-1])++descending;}
        if(descending!=1||ids.back()!=246795)fail("map_order_or_tail");
        w.put(whost.data());map.put(mhost.data());mexpected=map.get();
        // Exact original MTP raw-copy gather path; no quantization/repacking.
        k::gather_rows(w.data(),ROW,reinterpret_cast<const int32_t*>(map.data()),NO,compact.data(),stream);
        ck(cudaStreamSynchronize(stream),"gather_sync");
        verify_weights(true);
        std::printf("GATHER rows=%d row_bytes=%d full_bytes=%zu compact_bytes=%zu map_unique=1 map_in_range=1 descending_edges=1 tail_source_id=%d raw_rows_equal=1 guards=1 ok=1\n",NO,ROW,WB,CB,ids.back());
    }
    void verify_weights(bool initial){
        // Bounded 1024-row readback, no weights in logs/dumps. Compare every byte.
        constexpr size_t chunk_rows=1024;std::vector<unsigned char>buf(chunk_rows*ROW);
        for(size_t row=0;row<NS;row+=chunk_rows){size_t nr=std::min(chunk_rows,size_t(NS)-row),nb=nr*ROW;
            ck(cudaMemcpy(buf.data(),w.data()+row*ROW,nb,cudaMemcpyDeviceToHost),"head_readback");
            if(std::memcmp(buf.data(),whost.data()+row*ROW,nb))fail("full_head_bytes_changed");
        }
        for(size_t row=0;row<NO;row+=chunk_rows){size_t nr=std::min(chunk_rows,size_t(NO)-row),nb=nr*ROW;
            ck(cudaMemcpy(buf.data(),compact.data()+row*ROW,nb,cudaMemcpyDeviceToHost),"gather_readback");
            for(size_t j=0;j<nr;++j)if(std::memcmp(buf.data()+j*ROW,whost.data()+size_t(ids[row+j])*ROW,ROW))fail("gather_raw_row_mismatch");
        }
        if(!w.guards()||!compact.guards()||map.get()!=mexpected)fail("weight_or_map_guard");
        if(!initial)std::puts("WEIGHTS phase=post_timing full_head_equal=1 compact_rows_equal=1 guards=1 ok=1");
    }
    void make(int pat){
        pattern=pat;std::vector<float>x(NI);uint32_t rng=0x20261022u;
        for(int i=0;i<NI;++i){
            rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
            if(pat==0)x[i]=float(int32_t(rng&65535)-32768)*0x1p-15f;
            else if(pat==1)x[i]=asfloat((i&1)?0x80000000u:0u);
            else if(pat==2){const float scales[]={0x1p-10f,0.03125f,1.f,8.f};x[i]=float(int32_t(rng&65535)-32768)*0x1p-15f*scales[(i/32)%4];}
            else fail("pattern");
        }
        xf.put(x.data());k::native_quantize_q8_1(reinterpret_cast<const float*>(xf.data()),q.data(),NI,1,stream);
        ck(cudaStreamSynchronize(stream),"quantize_once_outside_timing");
        if(!xf.guards()||!q.guards())fail("quantizer_guard");
        xexpected=xf.get();qexpected=q.get();if(!pat){saved_x0=xexpected;saved_q0=qexpected;}
        // Q8_1 contract: both fp16 d/s fields finite, with exactly 80 blocks.
        for(size_t off=G;off<G+QB;off+=36)for(int j=0;j<4;j+=2){uint16_t h;std::memcpy(&h,qexpected.data()+off+j,2);if((h&0x7c00)==0x7c00)fail("nonfinite_q8_scale_or_sum");}
        std::printf("INPUT pattern=%d kind=%s x_hash=%016llx q8_hash=%016llx map_hash=%016llx quantizations=1 ok=1\n",
            pat,pat==0?"seeded_finite":pat==1?"signed_zero":"varied_finite_scale",
            (unsigned long long)hash(xexpected),(unsigned long long)hash(qexpected),(unsigned long long)hash(mexpected));
    }
    void restore0(){pattern=0;xexpected=saved_x0;qexpected=saved_q0;xf.put(xexpected.data()+G);q.put(qexpected.data()+G);std::puts("RESTORE pattern=0 same_input_bytes=1 quantizations=0 ok=1");}
    void launch(bool indexed){
        setenv("STRATA_GFX906_Q5_HEAD_58963_R2", (indexed || base_r2) ? "1" : "0", 1);
        if(indexed)k::native_q5_k_mtp_head_indexed_component(w.data(),q.data(),reinterpret_cast<float*>(b.data()),reinterpret_cast<const int*>(map.data()),NI,NS,NO,1,stream);
        else k::native_q5_k_mmvq(compact.data(),q.data(),reinterpret_cast<float*>(a.data()),NI,NO,1,stream);
    }
    bool unchanged()const{return xf.get()==xexpected&&q.get()==qexpected&&map.get()==mexpected&&w.guards()&&compact.guards();}
};
struct ElfSymbols{
    std::vector<unsigned char> data;
    ElfSymbols(){
        FILE*f=std::fopen("/proc/self/exe","rb");if(!f)fail("elf_open");
        if(std::fseek(f,0,SEEK_END)||std::ftell(f)<0)fail("elf_size");long n=std::ftell(f);
        if(n<64||n>256*1024*1024)fail("elf_size_bound");data.resize(size_t(n));
        std::rewind(f);if(std::fread(data.data(),1,data.size(),f)!=data.size()||std::fclose(f))fail("elf_read");
        const auto*h=header();if(std::memcmp(h->e_ident,ELFMAG,SELFMAG)||h->e_ident[EI_CLASS]!=ELFCLASS64||
            h->e_ident[EI_DATA]!=ELFDATA2LSB||h->e_shentsize!=sizeof(Elf64_Shdr))fail("elf_format");
    }
    const Elf64_Ehdr*header()const{return reinterpret_cast<const Elf64_Ehdr*>(data.data());}
    const unsigned char*range(uint64_t off,uint64_t n)const{if(off>data.size()||n>data.size()-off)fail("elf_bounds");return data.data()+off;}
    std::string symbol(void*func,uintptr_t&base,uint64_t&offset,int&kind)const{
        Dl_info info{};if(!dladdr(func,&info)||!info.dli_fbase)fail("elf_dladdr");
        base=reinterpret_cast<uintptr_t>(info.dli_fbase);auto*h=header();
        offset=reinterpret_cast<uintptr_t>(func)-(h->e_type==ET_DYN?base:0);
        auto*sections=reinterpret_cast<const Elf64_Shdr*>(range(h->e_shoff,uint64_t(h->e_shnum)*sizeof(Elf64_Shdr)));
        std::string found;
        for(int i=0;i<h->e_shnum;++i)if(sections[i].sh_type==SHT_SYMTAB){
            const auto&s=sections[i];if(s.sh_link>=h->e_shnum||s.sh_entsize!=sizeof(Elf64_Sym))fail("elf_symtab");
            auto*syms=reinterpret_cast<const Elf64_Sym*>(range(s.sh_offset,s.sh_size));
            const auto&strsec=sections[s.sh_link];auto*strs=reinterpret_cast<const char*>(range(strsec.sh_offset,strsec.sh_size));
            for(size_t j=0;j<s.sh_size/sizeof(Elf64_Sym);++j)if(syms[j].st_value==offset&&(ELF64_ST_TYPE(syms[j].st_info)==STT_FUNC||ELF64_ST_TYPE(syms[j].st_info)==STT_OBJECT)){
                if(syms[j].st_name>=strsec.sh_size)fail("elf_symbol_name");
                const char*name=strs+syms[j].st_name;if(!std::memchr(name,0,strsec.sh_size-syms[j].st_name))fail("elf_symbol_string");
                if((std::strstr(name,"native_mmvq_wave_kernel")||std::strstr(name,"native_q5_k_mtp_head_indexed_wave_kernel"))){if(!found.empty()&&found!=name)fail("elf_ambiguous_symbol");found=name;kind=ELF64_ST_TYPE(syms[j].st_info);}
            }
        }
        if(found.empty())fail("captured_host_function_missing_exact_elf_symbol");return found;
    }
};

struct Captured {cudaGraph_t graph=nullptr;cudaGraphExec_t exec=nullptr;void*func=nullptr;};
Captured capture(Fixture&f,bool indexed,const ElfSymbols&elf){
    ck(cudaStreamSynchronize(stream),"pre_capture");Captured c;
    ck(cudaStreamBeginCapture(stream,cudaStreamCaptureModeThreadLocal),"capture_begin");
    f.launch(indexed);ck(cudaStreamEndCapture(stream,&c.graph),"capture_end");
    size_t n=0;ck(cudaGraphGetNodes(c.graph,nullptr,&n),"graph_count");if(n!=1)fail("graph_not_one_node");
    cudaGraphNode_t node;ck(cudaGraphGetNodes(c.graph,&node,&n),"graph_node");
    cudaGraphNodeType type;ck(cudaGraphNodeGetType(node,&type),"graph_type");if(type!=cudaGraphNodeTypeKernel)fail("graph_not_kernel");
    cudaKernelNodeParams p{};ck(cudaGraphKernelNodeGetParams(node,&p),"graph_params");c.func=p.func;
    uintptr_t base=0;uint64_t offset=0;int kind=0;std::string sym=elf.symbol(p.func,base,offset,kind);
    std::string expected_object=indexed?INDEX_OBJECT:BASE_OBJECT, expected_func=indexed?INDEX_FUNC:BASE_FUNC;
    if(!indexed&&!base_r2){
        expected_object.replace(expected_object.find("Li2EE"),5,"Li1EE");
        expected_func.replace(expected_func.find("Li2EE"),5,"Li1EE");
    }
    bool symbol=(kind==STT_OBJECT&&sym==expected_object)||(kind==STT_FUNC&&sym==expected_func);
    bool shape=p.gridDim.x==unsigned((NO+(indexed||base_r2?8:4)-1)/(indexed||base_r2?8:4))&&p.gridDim.y==1&&p.gridDim.z==1&&p.blockDim.x==256&&p.blockDim.y==1&&p.blockDim.z==1&&p.sharedMemBytes==0;
    std::printf("GRAPH role=%c nodes=1 fn=%p image_base=%p elf_offset=0x%llx symbol=%s symbol_kind=%s grid=%u,%u,%u block=%u,%u,%u shared=%u symbol_ok=%d shape_ok=%d ok=%d\n",
      indexed?'B':'A',p.func,reinterpret_cast<void*>(base),(unsigned long long)offset,sym.c_str(),kind==STT_OBJECT?"OBJECT":"FUNC",
      p.gridDim.x,p.gridDim.y,p.gridDim.z,p.blockDim.x,p.blockDim.y,p.blockDim.z,p.sharedMemBytes,int(symbol),int(shape),int(symbol&&shape));
    if(!symbol||!shape)fail("graph_admission");
    ck(cudaGraphInstantiate(&c.exec,c.graph,0ull),"graph_instantiate");return c;
}
void reject_invalid(Fixture&f){
    // Only capture-time, host-rejected invalid arguments. Never execute invalid pointers/IDs.
    for(int test=0;test<14;++test){
        const void*w=f.w.data(),*q=f.q.data();float*y=reinterpret_cast<float*>(f.b.data());
        const int*m=reinterpret_cast<const int*>(f.map.data());int ni=NI,ns=NS,no=NO,nc=1;void*s=stream;
        if(test==0)ni=NI-1;if(test==1)ns=NS-1;if(test==2)no=NO-1;if(test==3)nc=2;
        if(test==4)w=nullptr;if(test==5)q=nullptr;if(test==6)y=nullptr;if(test==7)m=nullptr;
        if(test==8)w=f.w.data()+1;if(test==9)q=f.q.data()+1;
        if(test==10)y=reinterpret_cast<float*>(f.b.data()+1);if(test==11)m=reinterpret_cast<const int*>(f.map.data()+1);if(test==12)s=nullptr;
        if(test==13)setenv("STRATA_GFX906_Q5_HEAD_58963_R2","0",1);
        cudaGraph_t graph=nullptr;bool refused=false;ck(cudaStreamBeginCapture(stream,cudaStreamCaptureModeThreadLocal),"reject_capture_begin");
        try{k::native_q5_k_mtp_head_indexed_component(w,q,y,m,ni,ns,no,nc,s);}catch(const std::invalid_argument&){refused=true;}
        ck(cudaStreamEndCapture(stream,&graph),"reject_capture_end");size_t n=0;ck(cudaGraphGetNodes(graph,nullptr,&n),"reject_nodes");ck(cudaGraphDestroy(graph),"reject_destroy");
        if(!refused||n)fail("invalid_api_not_rejected_before_launch");
        setenv("STRATA_GFX906_Q5_HEAD_58963_R2","1",1);
        std::printf("REJECT case=%d invalid_argument=1 nodes=0 ok=1\n",test);
    }
}
std::vector<unsigned char> check(Fixture&f,Files&files,int phase,const std::vector<unsigned char>*reference){
    ck(cudaStreamSynchronize(stream),"check_sync");auto a=f.a.get(),b=f.b.get();
    size_t diff=0,guard_bad=0,nonfinite=0,unwritten=0,nonzero=0,reference_diff=0;
    for(size_t i=0;i<a.size();++i){diff+=a[i]!=b[i];if(i<G||i>=G+YB)guard_bad+=a[i]!=0x7f||b[i]!=0x7f;if(reference)reference_diff+=a[i]!=(*reference)[i]||b[i]!=(*reference)[i];}
    for(int i=0;i<NO;++i){uint32_t u;std::memcpy(&u,a.data()+G+size_t(i)*4,4);float v=asfloat(u);nonfinite+=!std::isfinite(v);unwritten+=u==SENT;nonzero+=(u&0x7fffffff)!=0;}
    uint32_t ta,tb;std::memcpy(&ta,a.data()+G+YB-4,4);std::memcpy(&tb,b.data()+G+YB-4,4);
    bool immutable=f.unchanged(),zero_ok=f.pattern==1?nonzero==0:nonzero>0;
    bool ok=!diff&&!guard_bad&&!nonfinite&&!unwritten&&!reference_diff&&immutable&&zero_ok&&ta==tb;
    std::printf("CHECK record=%d phase=%d pattern=%d byte_diff=%zu guard_bad=%zu nonfinite=%zu unwritten=%zu reference_diff=%zu nonzero=%zu inputs_unchanged=%d tail_source_id=%d tail_A=%08x tail_B=%08x ok=%d\n",
      files.records,phase,f.pattern,diff,guard_bad,nonfinite,unwritten,reference_diff,nonzero,int(immutable),f.ids.back(),ta,tb,int(ok));
    if(!ok)fail("numerical_or_guard_mismatch");
    files.record(phase,f.pattern,f.xexpected,f.qexpected,f.mexpected,a,b);
    return a;
}
double median(std::vector<double>v){std::sort(v.begin(),v.end());size_t n=v.size();return n%2?v[n/2]:(v[n/2-1]+v[n/2])/2;}
double p95(std::vector<double>v){std::sort(v.begin(),v.end());return v[(95*v.size()+99)/100-1];}
struct Timer {
    cudaEvent_t start=nullptr,end=nullptr;
    Timer(){ck(cudaEventCreate(&start),"event");ck(cudaEventCreate(&end),"event");}
    ~Timer(){ck(cudaEventDestroy(start),"event_destroy");ck(cudaEventDestroy(end),"event_destroy");}
    double once(const std::function<void()>&fn){ck(cudaEventRecord(start,stream),"event_start");fn();ck(cudaEventRecord(end,stream),"event_end");ck(cudaEventSynchronize(end),"event_sync");float ms=0;ck(cudaEventElapsedTime(&ms,start,end),"event_elapsed");if(!std::isfinite(ms)||ms<=0)fail("invalid_time");return 1000.0*ms;}
};
void measure(Fixture&f,Files&files,const Captured&ga,const Captured&gb,int iters,bool reverse,bool graph){
    auto A=[&]{if(graph)ck(cudaGraphLaunch(ga.exec,stream),"graph_A");else f.launch(false);};
    auto B=[&]{if(graph)ck(cudaGraphLaunch(gb.exec,stream),"graph_B");else f.launch(true);};
    for(int i=0;i<8;++i){f.a.reset();f.b.reset();if((i&1)^reverse){B();A();}else{A();B();}}
    ck(cudaStreamSynchronize(stream),"warm_sync");Timer t;std::vector<double>a,b,ratios,deltas;
    for(int pair=0;pair<iters;++pair){double x,y;bool ba=(pair&1)^reverse;
        // Identical output reset immediately before its event, excluded from timing.
        if(ba){f.b.reset();y=t.once(B);f.a.reset();x=t.once(A);}else{f.a.reset();x=t.once(A);f.b.reset();y=t.once(B);}
        a.push_back(x);b.push_back(y);ratios.push_back(x/y);deltas.push_back(x-y);
        std::fprintf(files.timing,"%s,%d,%s,%.9f,%.9f\n",graph?"graph":"direct",pair,ba?"BA":"AB",x,y);
    }
    std::printf("TIMING metric=%s pairs=%d first=%s A_median_us=%.9f B_median_us=%.9f A_p95_us=%.9f B_p95_us=%.9f paired_speedup_median=%.9f paired_delta_us_median=%.9f resets_outside_events=1 ok=1\n",graph?"graph":"direct",iters,reverse?"BA":"AB",median(a),median(b),p95(a),p95(b),median(ratios),median(deltas));
    check(f,files,graph?3:2,&f.reference0); // Actual last timed outputs, no extra launch/reset.
}
int number(const char*x){char*e=nullptr;long n=std::strtol(x,&e,10);if(!*x||*e||n<0||n>10000)fail("numeric_arg");return int(n);}
} // namespace
int main(int argc,char**argv){
    static_assert(sizeof(float)==4&&sizeof(int32_t)==4&&sizeof(int)==4);
    std::setvbuf(stdout,nullptr,_IOLBF,0);int device=-1,iters=0,reverse=-1;std::string gguf,vocab,dump;
    for(int i=1;i<argc;++i){
        if(!std::strcmp(argv[i],"--device")&&i+1<argc)device=number(argv[++i]);
        else if(!std::strcmp(argv[i],"--iters")&&i+1<argc)iters=number(argv[++i]);
        else if(!std::strcmp(argv[i],"--reverse")&&i+1<argc)reverse=number(argv[++i]);
        else if(!std::strcmp(argv[i],"--gguf")&&i+1<argc)gguf=argv[++i];
        else if(!std::strcmp(argv[i],"--vocab")&&i+1<argc)vocab=argv[++i];
        else if(!std::strcmp(argv[i],"--dump")&&i+1<argc)dump=argv[++i];
        else fail("usage_device_iters_reverse_gguf_vocab_dump");
    }
    if(device<0||iters!=200||reverse<0||reverse>1||gguf.empty()||vocab.empty()||dump.empty())fail("required_args");
    uint32_t endian=1;if(*(unsigned char*)&endian!=1)fail("little_endian");
    if(std::strcmp(env("STRATA_GFX906_Q5_HEAD_R2"),"1") || std::strcmp(env("STRATA_MMVQ_WAVE"),"1"))fail("fixed_selector_environment");
    const char* br=env("STRATA_MTP58963_BASE_R2");if(std::strcmp(br,"0")&&std::strcmp(br,"1"))fail("base_r2_selector");
    base_r2=std::strcmp(br,"1")==0;
    std::printf("ARM baseline_contiguous_R=%d candidate_indexed_R=2 shortlist=58963\n",base_r2?2:1);
    // Host fixture and map validity are established before any GPU call.
    auto wh=read_fixture(gguf,true),mh=read_fixture(vocab,false);std::vector<unsigned char>seen(NS,0);
    for(int i=0;i<NO;++i){int32_t id;std::memcpy(&id,mh.data()+i*4,4);if(id<0||id>=NS||seen[id])fail("pre_gpu_map_range_or_duplicate");seen[id]=1;}
    std::printf("FIXTURE head_offset=%llu head_bytes=%zu compact_bytes=%zu row_bytes=%d head_sha256=%s vocab_sha256=%s stat_pins=1 external_sha_verification_required=1\n",PIN_HEAD_OFFSET,WB,CB,ROW,PIN_HEAD_SHA,PIN_VOCAB_SHA);
    int count=0;ck(cudaGetDeviceCount(&count),"device_count");if(device>=count)fail("device_range");
    ck(cudaSetDevice(device),"set_device");cudaDeviceProp p{};ck(cudaGetDeviceProperties(&p,device),"properties");
#if defined(STRATA_HIP_GFX906)
    if(p.warpSize!=64||std::strncmp(p.gcnArchName,"gfx906",6)||(p.gcnArchName[6]&&p.gcnArchName[6]!=':'))fail("not_gfx906_wave64");
    char pci[64]={};ck(hipDeviceGetPCIBusId(pci,sizeof(pci),device),"pci");
    std::printf("META device=%d pci=%s arch=%s warp=%d l2_bytes=%d iters=%d reverse=%d input_bytes=%zu map_bytes=%zu output_bytes=%zu cold_hbm_claim=0\n",device,pci,p.gcnArchName,p.warpSize,p.l2CacheSize,iters,reverse,QB,MB,YB);
#else
    fail("gfx906_build_required");
#endif
    ck(cudaStreamCreate(&stream),"stream");Files files(dump);ElfSymbols elf;
    {
        Fixture f(std::move(wh),std::move(mh));f.make(0);
        // Warm static dispatch outside capture, then validate exact registered functions.
        f.a.reset();f.b.reset();f.launch(false);f.launch(true);ck(cudaStreamSynchronize(stream),"dispatch_warm");
        Captured ga=capture(f,false,elf),gb=capture(f,true,elf);if(ga.func==gb.func)fail("same_function");
        std::puts("ADMISSION geometry=2560,248320,58963,1 distinct_functions=1 ok=1");reject_invalid(f);
        for(int pat=0;pat<3;++pat){
            if(pat)f.make(pat);
            f.a.reset();f.b.reset();f.launch(false);f.launch(true);auto direct=check(f,files,0,nullptr);
            if(!pat)f.reference0=direct;
            f.a.reset();f.b.reset();ck(cudaGraphLaunch(ga.exec,stream),"parity_graph_A");ck(cudaGraphLaunch(gb.exec,stream),"parity_graph_B");check(f,files,1,&direct);
        }
        f.restore0();measure(f,files,ga,gb,iters,reverse,false);measure(f,files,ga,gb,iters,reverse,true);
        f.verify_weights(false);
        ck(cudaGraphExecDestroy(ga.exec),"graph_exec_destroy");ck(cudaGraphExecDestroy(gb.exec),"graph_exec_destroy");
        ck(cudaGraphDestroy(ga.graph),"graph_destroy");ck(cudaGraphDestroy(gb.graph),"graph_destroy");
    }
    ck(cudaStreamDestroy(stream),"stream_destroy");files.close();
    std::printf("DUMP records=%d bytes=%llu expected_bytes=%llu\n",CASES,(unsigned long long)files.bytes,(unsigned long long)DUMP_BYTES);
    std::puts("RESULT status=PASS parity_records=6 post_timing_records=2 timed_metrics=2 rejected_api_cases=14");return 0;
}
