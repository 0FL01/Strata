#include "../../src/prefill/hc_bf16_clone_gate.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <initializer_list>
namespace strata::prefill::hc_bf16_clone {
thread_local Token* active=nullptr;
[[noreturn]] void fatal(const char*){std::abort();}
}
namespace c=strata::prefill::hc_bf16_clone;
int main(){
 assert(c::runtime_enabled(nullptr)&&c::runtime_enabled("1"));
 for(const char* value:{"","0","00","01","10","true","false"," 1","1 ","-1","2"})
  assert(!c::runtime_enabled(value));
 assert(!c::exact_one(nullptr)&&!c::exact_one("")&&!c::exact_one("0")&&!c::exact_one("01")&&!c::exact_one("10")&&!c::exact_one("true")&&c::exact_one("1"));
 uint16_t x=0,w=0;float y=0;uint64_t counts[2]={};void* stream=&counts;
 for(int role=0;role<2;++role)for(int T:{4096,4093}){
  int N=role?10240:320,K=role?320:10240;
  c::Scope scope(true,role,0,T,N,K,stream,&x,&w,&y,counts);
  assert(c::active==&scope.value);
  auto check=[&](int64_t t,int64_t n,int64_t k,int64_t ldy,float beta,int64_t ldx,bool xf,bool fio){
   return c::matches(scope.value,&x,&w,&y,stream,t,n,k,ldy,beta,ldx,xf,fio);
  };
  assert(check(T,N,K,N,0,0,false,false));
  assert(!check(T-1,N,K,N,0,0,false,false));
  assert(!check(T,N+1,K,N,0,0,false,false));
  assert(!check(T,N,K+1,N,0,0,false,false));
  assert(!check(T,N,K,N+1,0,0,false,false));
  assert(!check(T,N,K,N,1,0,false,false));
  assert(!check(T,N,K,N,0,K+1,false,false));
  assert(!check(T,N,K,N,0,0,true,false));
  assert(!check(T,N,K,N,0,0,false,true));
  assert(!c::matches(scope.value,&w,&w,&y,stream,T,N,K,N,0,0,false,false));
  assert(!c::matches(scope.value,&x,&x,&y,stream,T,N,K,N,0,0,false,false));
  assert(!c::matches(scope.value,&x,&w,&y,nullptr,T,N,K,N,0,0,false,false));
  scope.value.used=true;assert(!check(T,N,K,N,0,0,false,false));
 }
 assert(!c::active);
 {c::Scope off(false,0,0,4096,320,10240,stream,&x,&w,&y,counts);assert(!c::active);}
 assert(!c::shape(2,4096,320,10240)&&!c::shape(0,4096,10240,320));
 puts("CLONE_GATE_PASS");
}
