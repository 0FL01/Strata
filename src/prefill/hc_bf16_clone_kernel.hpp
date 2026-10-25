#pragma once
#include <cstdint>
#include <cstddef>
#ifndef HC_LDS_INDEX_ONLY
#include <hip/hip_runtime.h>
#define HC_LDS_HD __host__ __device__
#else
#define HC_LDS_HD
#endif
namespace hc_lds {
HC_LDS_HD constexpr unsigned local_m(unsigned t,unsigned i){return 2*(t%16)+i%2+32*(i/2);}
HC_LDS_HD constexpr unsigned local_n(unsigned t,unsigned j){return 2*(t/16)+j;}
HC_LDS_HD constexpr unsigned stagger_mask(unsigned K){
 unsigned c=32;while(c>=2&&(c<<4)>K/8)c>>=1;return c?c-1:0;
}
HC_LDS_HD constexpr unsigned k_start(unsigned m,unsigned K){return (m&stagger_mask(K))*128;}
HC_LDS_HD constexpr unsigned cyclic_k(unsigned s,unsigned o,unsigned K){return s+o<K?s+o:s+o-K;}
HC_LDS_HD constexpr bool x_first(unsigned i,unsigned j){return j==1&&i!=3;}
#ifndef HC_LDS_INDEX_ONLY
__device__ __forceinline__ float expand(uint16_t b){return __uint_as_float(uint32_t(b)<<16);}
__device__ __forceinline__ float read_lds(uint16_t b){return expand(b);}
__device__ __forceinline__ float read_lds(float b){return b;}
template<class S> __device__ __forceinline__ S stage(uint16_t b);
template<> __device__ __forceinline__ uint16_t stage<uint16_t>(uint16_t b){return b;}
template<> __device__ __forceinline__ float stage<float>(uint16_t b){return expand(b);}
__device__ __forceinline__ float ordered_fmac(float a,float b,float c){
 asm volatile("v_fmac_f32 %0, %1, %2" : "+v"(c) : "v"(a),"v"(b));return c;
}
__device__ __forceinline__ float alpha_one(float a){
 float r;asm volatile("v_mul_f32 %0, 1.0, %1" : "=v"(r) : "v"(a));return r;
}
template<class S>
__global__ __launch_bounds__(256) void kernel(const uint16_t* __restrict__ W,
 const uint16_t* __restrict__ X,float* __restrict__ Y,unsigned N,unsigned T,unsigned K){
 __shared__ S tile[768]; // W[8][64],X[8][32]:1536/3072 bytes.
 unsigned tid=threadIdx.x,mt=blockIdx.x,nt=blockIdx.y;
 unsigned mb=64*mt,nb=32*nt,start=k_start(mt,K);
 float acc[2][4]={{0,0,0,0},{0,0,0,0}};
 for(unsigned off=0;off<K;off+=8){
  unsigned kb=cyclic_k(start,off,K);
  unsigned wm=tid/4,wk=2*(tid%4),xn=tid/8,xk=tid%8;
  unsigned m=mb+wm,n=nb+xn;
  m=m<N?m:N-1;n=n<T?n:T-1; // Installed tail-load clamp.
  uint16_t a=W[size_t(m)*K+kb+wk],b=W[size_t(m)*K+kb+wk+1];
  uint16_t x=X[size_t(n)*K+kb+xk];
  tile[wk*64+wm]=stage<S>(a);tile[(wk+1)*64+wm]=stage<S>(b);
  tile[512+xk*32+xn]=stage<S>(x);
  __syncthreads();
#pragma unroll
  for(unsigned k=0;k<8;++k){
   float w[4],x[2];
#pragma unroll
   for(unsigned i=0;i<4;++i)w[i]=read_lds(tile[k*64+local_m(tid,i)]);
#pragma unroll
   for(unsigned j=0;j<2;++j)x[j]=read_lds(tile[512+k*32+local_n(tid,j)]);
#pragma unroll
   for(unsigned j=0;j<2;++j){
#pragma unroll
    for(unsigned i=0;i<4;++i)
     acc[j][i]=x_first(i,j)?ordered_fmac(x[j],w[i],acc[j][i]):ordered_fmac(w[i],x[j],acc[j][i]);
   }
  }
  __syncthreads(); // Consumers finish before next tile overwrite.
 }
#pragma unroll
 for(unsigned j=0;j<2;++j){
#pragma unroll
  for(unsigned i=0;i<4;++i){
   unsigned m=mb+local_m(tid,i),n=nb+local_n(tid,j);
   if(m<N&&n<T)Y[size_t(n)*N+m]=alpha_one(acc[j][i]);
  }
 }
}
// Async launch only; caller owns gfx906/FP-mode gate and synchronization.
inline hipError_t launch(bool fp32,const uint16_t* W,const uint16_t* X,float* Y,
 int N,int T,int K,hipStream_t stream){
 if(!W||!X||!Y||!((N==320&&K==10240)||(N==10240&&K==320))||
    !(T==4096||T==4093))return hipErrorInvalidValue;
 dim3 grid((N+63)/64,(T+31)/32),block(256);
 if(fp32)hipLaunchKernelGGL((kernel<float>),grid,block,0,stream,W,X,Y,N,T,K);
 else hipLaunchKernelGGL((kernel<uint16_t>),grid,block,0,stream,W,X,Y,N,T,K);
 return hipGetLastError();
}
#endif
}
#undef HC_LDS_HD
