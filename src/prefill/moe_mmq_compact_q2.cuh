// Compact outer scheduler adapted from llama.cpp mmq.cuh at
// 3cf03257f219afbe7334045ff7c6a06ac68c627d. Tile arithmetic remains upstream.
// MIT License
// Copyright (c) 2023-2026 The ggml authors
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
#if defined(STRATA_HIP_GFX906) && defined(__HIPCC__) && defined(STRATA_GFX906_COMPACT_MMQ_BUILT)
struct CompactPrefix { int offsets[17] = {}; };
__global__ __launch_bounds__(256,2)
void compact_q2_j48(mmq_args a, CompactPrefix prefix) {
    constexpr int J=48, I=64;
#if defined(__HIP_DEVICE_COMPILE__) && __HIP_DEVICE_COMPILE__
    static_assert(ggml_cuda_get_physical_warp_size()==64);
    static_assert(ggml_cuda_mmq_get_I(GGML_TYPE_Q2_0,48,false)==64);
    static_assert(ggml_cuda_mmq_get_nthreads(GGML_TYPE_Q2_0,48,false)==256);
    static_assert(ggml_cuda_mmq_get_K_vram(GGML_TYPE_Q2_0,48,false)==256);
    static_assert(!ggml_cuda_mmq_get_stream_k(GGML_TYPE_Q2_0,48,false));
#endif
    const int tile=blockIdx.y;
    int lo=0,hi=16;
    while (lo+1<hi) { const int mid=(lo+hi)/2; if (prefix.offsets[mid]<=tile) lo=mid; else hi=mid; }
    const int e=lo, jt=tile-prefix.offsets[e], it=blockIdx.x;
    const int low=a.expert_bounds[e], count=a.expert_bounds[e+1]-low;
    extern __shared__ int ids[];
    const int tid=threadIdx.y*64+threadIdx.x;
    if (tid<J) ids[tid]=a.ids_dst[low+jt*J+tid];
    __syncthreads();
    const int offset_y=(low+jt*J)*(sizeof(block_q8_1_mmq)/sizeof(int));
    const int offset_x=e*(int)a.stride_channel_x+it*I*(int)a.stride_row_x;
    mul_mat_q_process_tile<GGML_TYPE_Q2_0,J,false,false>(
        a.x,offset_x,a.y+offset_y,ids,a.dst+it*I,nullptr,nullptr,
        (int)a.stride_row_x,(int)a.ncols_y,(int)a.nrows_dst,
        (int)a.nrows_x-it*I-1,count-jt*J-1,0,
        (int)a.ncols_x/ggml_cuda_type_traits<GGML_TYPE_Q2_0>::qk);
}
bool try_compact_q2_j48(const Product& p,const mmq_args& a,cudaStream_t stream) {
    if (!p.compact_tiles || !p.host_counts_valid || !p.local_full_routing_prefill ||
        p.type!=GGML_TYPE_Q2_0 || p.n!=16 || p.tab || p.y_scale || !p.w || !p.xq || !p.dst ||
        !p.ids || !p.bounds || a.ncols_opt!=48 || p.total_rows<=0 || p.total_rows>40960 ||
        p.max_rows<=0 || p.max_rows>4096 || p.max_rows>p.total_rows || p.ld_dst!=p.w_rows ||
        !((p.w_rows==1280 && p.w_cols==2560)||(p.w_rows==2560 && p.w_cols==640)) ||
        p.expert_bytes!=matrix_bytes(p.type,p.w_rows,p.w_cols)) return false;
    const int id=ggml_cuda_get_device(); const auto& info=ggml_cuda_info();
    if (id<0 || id>=info.device_count) return false;
    const auto& dev=info.devices[id];
    if (dev.cc!=GGML_CUDA_CC_VEGA20 || dev.warp_size!=64 || dev.physical_device!=id ||
        dev.physical_share_count!=1 || dev.virtual_index!=0) return false;
    // Same selection as upstream, including strict first-minimum tie breaking.
    int selected=0,best=INT_MAX;
    for (int j=8;j<=128 && best>1;j+=8) {
        const auto c=ggml_cuda_mmq_get_config(GGML_TYPE_Q2_0,j,false,dev.cc);
        if (c.type==GGML_TYPE_COUNT || mmq_get_nbytes_shared(c,dev.cc)>dev.smpbo) continue;
        const int tiles=(a.ncols_opt+c.J-1)/c.J;
        if (tiles<best) {best=tiles;selected=j;}
    }
    if (selected!=48) return false;
    const auto c=ggml_cuda_mmq_get_config(GGML_TYPE_Q2_0,48,false,dev.cc);
    if (c.type!=GGML_TYPE_Q2_0 || c.I!=64 || c.J!=48 || c.K_vram!=256 ||
        c.nthreads!=256 || c.occupancy!=2 || c.stream_k ||
        c.sram_layout!=GGML_CUDA_MMQ_SRAM_LAYOUT_Q8_0) return false;
    CompactPrefix prefix; int64_t sum=0,max_count=0;
    for (int e=0;e<16;++e) {
        const int64_t count=p.host_counts[e];
        if (count<0 || count>p.max_rows) return false;
        sum+=count;max_count=std::max(max_count,count);
        const int64_t next=(int64_t)prefix.offsets[e]+(count+47)/48;
        if (next>INT32_MAX) return false;
        prefix.offsets[e+1]=(int)next;
    }
    if (max_count!=p.max_rows || sum>p.total_rows || prefix.offsets[16]<=0) return false;
    const int shared=mmq_get_nbytes_shared(c,dev.cc);
    hipDeviceProp_t prop{};
    if (hipGetDeviceProperties(&prop,id)!=hipSuccess || std::strncmp(prop.gcnArchName,"gfx906",6)!=0 ||
        (prop.gcnArchName[6]!='\0' && prop.gcnArchName[6]!=':') || prop.warpSize!=64 ||
        shared>prop.sharedMemPerBlock || prop.maxGridSize[0]<p.w_rows/64 ||
        prop.maxGridSize[1]<prefix.offsets[16]) return false;
    compact_q2_j48<<<dim3(p.w_rows/64,prefix.offsets[16],1),dim3(64,4,1),shared,stream>>>(a,prefix);
    ck(cudaGetLastError(),"compact q2 j48");
    return true;
}
#else
bool try_compact_q2_j48(const Product&,const mmq_args&,cudaStream_t) {return false;}
#endif
