#!/usr/bin/env python3
"""Compile and run the actual extracted host eligibility block, without HIP/ROCm/GPU.

Compatibility definitions mirror the qualified runtime flags.make captured from the qualified build.
The real gfx_arch_is header is included; only CUDA property calls and input objects are mocked.
"""
from pathlib import Path
import subprocess, tempfile, json, hashlib, sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
source=(root/'src/program/generate.cpp').read_text()
a=source.index('            bool defer_primary_commit = false;')
b=source.index('            struct PrimaryCommitScope {',a)
block=source[a:b]
assert '#if defined(STRATA_USE_HIP) || defined(STRATA_HIP_GFX906)' in block
prefix=r'''
#include <cstdlib>
#include <cstring>
#include <iostream>
#include "strata/kernels/gfx_arch.hpp"
struct Config {
 bool enabled=true, force_sync=false, use_mtp=true;
 int batch=0,pipeline_windows=0;
 bool pipe=false,pl_ran=false,multi_gpu=true,split_same=false;
 int n_stages=2,dev0=0,dev1=1;
 const char* arch0="gfx906"; const char* arch1="gfx906:sramecc-:xnack-";
 int error0=0,error1=0;
};
struct cudaDeviceProp { char gcnArchName[64]{}; };
using cudaError_t=int; constexpr int cudaSuccess=0;
static Config current; static int queries=0,last_errors=0;
int cudaGetDeviceProperties(cudaDeviceProp* p,int dev) {
 ++queries; bool primary=dev==current.dev0;
 const char* arch=primary?current.arch0:current.arch1;
 std::strncpy(p->gcnArchName,arch,sizeof(p->gcnArchName)-1);
 return primary?current.error0:current.error1;
}
int cudaGetLastError(){++last_errors;return 0;}
struct Stage { int dev; int device()const{return dev;} };
bool eligible(Config c) {
 current=c;queries=last_errors=0;
 if(c.enabled)setenv("STRATA_PRIMARY_COMMIT_OVERLAP","",1);else unsetenv("STRATA_PRIMARY_COMMIT_OVERLAP");
 if(c.force_sync)setenv("STRATA_COMMIT_SYNC","0",1);else unsetenv("STRATA_COMMIT_SYNC");
 const bool use_mtp=c.use_mtp,pipe=c.pipe,pl_ran=c.pl_ran,multi_gpu=c.multi_gpu,split_same=c.split_same;
 const int n_stages=c.n_stages;
 struct {int batch,pipeline_windows;} o{c.batch,c.pipeline_windows};
 Stage stages[2]{{c.dev0},{c.dev1}};
 auto stage_ver=[&](int st)->Stage&{return stages[st];};
'''
suffix=r'''
 return defer_primary_commit;
}
int main(){
 int cases=0;
#if defined(STRATA_USE_HIP) || defined(STRATA_HIP_GFX906)
 const bool backend=true;
#else
 const bool backend=false;
#endif
 auto check=[&](const char* name,Config c,bool want,int want_queries){
  ++cases;
  bool got=eligible(c);
  if(got!=(backend&&want)||queries!=(backend?want_queries:0)){
   std::cerr<<"FAIL "<<name<<" got="<<got<<" queries="<<queries<<"\n";std::exit(2);
  }
 };
 Config c;
 check("two gfx906 with feature suffix",c,true,2);
 c.arch1="gfx906";check("two plain gfx906",c,true,2);
 c=Config{};c.enabled=false;check("opt-in missing",c,false,0);
 c=Config{};c.force_sync=true;check("force sync even value zero",c,false,0);
 c=Config{};c.use_mtp=false;check("non MTP",c,false,0);
 c=Config{};c.batch=1;check("batch",c,false,0);
 c=Config{};c.pipeline_windows=1;check("pipeline option",c,false,0);
 c=Config{};c.pipe=true;check("pipe active",c,false,0);
 c=Config{};c.pl_ran=true;check("pipeline already ran",c,false,0);
 c=Config{};c.multi_gpu=false;check("single GPU",c,false,0);
 c=Config{};c.split_same=true;check("split same",c,false,0);
 c=Config{};c.n_stages=1;check("one stage",c,false,0);
 c=Config{};c.n_stages=3;check("three stages",c,false,0);
 c=Config{};c.dev1=0;check("same device IDs",c,false,0);
 c=Config{};c.arch0="gfx908";check("primary wrong arch",c,false,2);
 c=Config{};c.arch1="gfx90a";check("secondary wrong arch",c,false,2);
 c=Config{};c.arch1="gfx9060";check("arch prefix rejected",c,false,2);
 c=Config{};c.arch1="";check("empty arch rejected",c,false,2);
 c=Config{};c.error0=1;check("primary property failure",c,false,2);
 if(last_errors!=(backend?1:0))return 3;
 c=Config{};c.error1=1;check("secondary property failure",c,false,2);
 if(last_errors!=(backend?1:0))return 3;
 c=Config{};c.error0=c.error1=1;check("both property failures",c,false,2);
 if(last_errors!=(backend?1:0))return 3;
 std::cout<<"PASS "<<cases<<" actual-block cases backend="<<backend<<"\n";
}
'''
compat=['STRATA_HIP_GFX906=1','STRATA_NATIVE_EXPERTS=1','STRATA_PREFILL_FUSED=1','STRATA_PREFILL_MMQ=1','STRATA_VERSION="0.1.40"','USE_PROF_API=1','__HIP_PLATFORM_AMD__=1']
results=[]
with tempfile.TemporaryDirectory(prefix='primary-commit-guard-') as td:
 p=Path(td);cpp=p/'guard.cpp';cpp.write_text(prefix+block+suffix)
 for name,defs in [('qualified_gfx906_compat',compat),('native_hip',['STRATA_USE_HIP=1']),('unsupported_backend',[])]:
  exe=p/name
  cmd=['c++','-std=c++17','-O0','-I',str(root/'include'),*[f'-D{x}' for x in defs],str(cpp),'-o',str(exe)]
  subprocess.run(cmd,check=True,capture_output=True,text=True)
  run=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
  results.append({'route':name,'definitions':defs,'result':run.stdout.strip()})
report={'passed':True,'kind':'compiled actual extracted host eligibility block with mock device calls','block_sha256':hashlib.sha256(block.encode()).hexdigest(),'routes':results,'engine_build_performed':False,'gpu_run_performed':False}
print(json.dumps(report,indent=2))

