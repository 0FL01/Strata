#!/usr/bin/env python3
"""Extract actual GEN/BGEN/GENI parser blocks and test without a native engine.
Requires g++ and a local git baseline. Vision/device/session behavior is NOT exercised.
Output artifacts are local; optional --retained files are never bundled in this source.
"""
from pathlib import Path
import hashlib,json,subprocess,os,sys,time,argparse,tempfile
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description="CPU-only exact source request-bounds checks; no GPU/runtime proof.")
ap.add_argument("--out", type=Path)
ap.add_argument("--baseline", default="f9b38e9e5d70cef7776f2a5bd6fed5e56872ec02")
ap.add_argument("--retained", type=Path, nargs="*", default=[])
args=ap.parse_args()
D=args.out or Path(tempfile.mkdtemp(prefix="strata-request-bounds-"))
D.mkdir(parents=True,exist_ok=True)
SRC=ROOT/"src/program/generate.cpp"
BASE=D/"baseline-generate.cpp"
BASE.write_bytes(subprocess.check_output(["git","-C",str(ROOT),"show",args.baseline+":src/program/generate.cpp"]))
s=SRC.read_text(); b=BASE.read_text()
T=D/'cpu-tests';T.mkdir(exist_ok=True)
def slice_between(txt,start,end):
 a=txt.index(start);z=txt.index(end,a)
 return txt[a:z]
helper=slice_between(s,'bool gen_request_fits_context(', 'bool parse_i64_list(')
def parser(txt):
 return slice_between(txt,'bool parse_i64_list(', '/// The pool')
assert parser(s)==parser(b),'token-list parser changed'
def prefix(txt):
 return slice_between(txt,'            const bool geni = line.rfind("GENI ", 0) == 0;', '            req_imgs.clear();')
old_guard=slice_between(b,'            if (n + max_new + 8 > o.max_context) {','            bool bad = false;')
pieces={'bounds_helper':helper,'token_parser':parser(s),'candidate_request_prefix':prefix(s),'baseline_request_prefix':prefix(b),'baseline_context_guard':old_guard}
(T/'extracted-source-sha256.json').write_text(json.dumps({k:hashlib.sha256(v.encode()).hexdigest() for k,v in pieces.items()},indent=2)+'\n')
head=r'''#include <algorithm>
#include <cassert>
#include <cerrno>
#include <charconv>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>
#include "strata/core/logit_bias.hpp"
// CPU-only adapter for a setter; the exact packet parser is extracted below.
// No engine, file embedding loader, device runtime, kernels, or GPU allocations are linked.
namespace strata::prefill {
struct Prefill { static inline double pipe = 0; static void set_pipe_request(double p) { pipe = p; } };
}
struct Result {
 long long max_new = 0; int64_t n = 0;
 std::vector<int64_t> ids; std::vector<float> bias; std::vector<uint64_t> img_keys;
 std::string emb_path, option_fingerprint;
 bool operator==(const Result&) const = default;
};
'''
tail=r'''
            result.max_new = max_new; result.n = n; result.ids = ids;
            result.bias = req_bias; result.img_keys = req_img_keys; result.emb_path = emb_path;
            std::ostringstream opts; opts << std::setprecision(17)
                << req_temperature << ' ' << req_top_p << ' ' << req_top_k << ' ' << req_seed << ' '
                << req_min_p << ' ' << req_penalty_repeat << ' ' << req_penalty_freq << ' '
                << req_penalty_present << ' ' << req_penalty_last_n << ' ' << req_bias_text << ' '
                << req_bias_present << ' ' << req_cvec << ' ' << req_ckpt << ' ' << req_pin << ' '
                << req_pcie_frac << ' ' << req_spec_min_p << ' ' << req_pipe << ' ' << req_aux_cpus << ' '
                << req_pcie_set << ' ' << strata::prefill::Prefill::pipe;
            result.option_fingerprint = opts.str();
            return true;
        }
        return false;
    }
}
'''
batch_prefix=slice_between(s, '            if (line.rfind("BGEN ", 0) == 0 ||', '            // #477:')
def wrapper(name,txt,extra=''):
 return ('namespace '+name+' {\n'+(helper if name=='candidate' else '')+parser(txt)+
 '''bool parse(std::string line, int64_t context, Result& result, int batch = 0, bool occupied = false) {
        struct { int64_t max_context; int batch = 0; double pcie_frac = 0.3, spec_min_p = 0.5; } o{context};
        o.batch = batch;
        const int S = 8;
        int admit_slot = -1; long long admit_max_new = 0;
        struct Slot { bool active = false; }; std::vector<Slot> bs((size_t) batch);
        if (!bs.empty()) bs[0].active = occupied;
        double line_drain_ms = 0, adm_drain_ms = 0;
        (void) S; (void) admit_slot; (void) admit_max_new; (void) line_drain_ms; (void) adm_drain_ms;
        const int64_t n_vocab = 200000; // Only used by the exact optional logit-bias parser.
        for (int once = 0; once != 1; ++once) {
'''+(batch_prefix if name=='candidate' else '')+prefix(txt)+extra+tail)
tests=r'''
static size_t checks = 0;
static void expect(bool good, const char* name) {
 ++checks;
 if (!good) { std::cerr << "FAIL " << name << '\n'; std::exit(1); }
}
static bool oracle(size_t n, long long out, int64_t ctx) {
 return n > 0 && out >= 1 && static_cast<__int128>(n) + static_cast<__int128>(out) + 8 <= static_cast<__int128>(ctx);
}
static void compare_valid(const std::string& request, int64_t ctx = 262144) {
 Result old_result, new_result;
 expect(baseline::parse(request, ctx, old_result), "baseline valid parse");
 errno = ERANGE; // The new strtoll must reset a stale caller errno.
 expect(candidate::parse(request, ctx, new_result), "candidate valid parse");
 expect(old_result == new_result, "unchanged valid packet, all ids and parsed options");
}
int main(int argc, char** argv) {

 if(argc > 1 && std::string(argv[1]) == "--probe") {
   for(int i=2;i<argc;++i) {
     Result r;
     const bool ok=candidate::parse(argv[i],20,r,2,std::getenv("OCCUPIED")!=nullptr);
     std::cout << "PROBE accepted=" << ok << " max_new=" << r.max_new << " ids=" << r.ids.size() << '\n';
   }
   return 0;
 }
 using candidate::gen_request_fits_context;
 expect(gen_request_fits_context(1,1,10), "minimum context valid");
 expect(!gen_request_fits_context(1,1,9), "minimum context one below");
 expect(!gen_request_fits_context(0,1,262144), "empty prompt");
 expect(!gen_request_fits_context(1,0,262144), "zero output");
 expect(!gen_request_fits_context(1,-1,262144), "negative output");
 expect(!gen_request_fits_context(1,LLONG_MIN,262144), "LLONG_MIN output");
 expect(!gen_request_fits_context(1,LLONG_MAX,262144), "LLONG_MAX output");
 expect(!gen_request_fits_context(1,1,INT64_MIN), "INT64_MIN context");
 expect(!gen_request_fits_context(SIZE_MAX,1,INT64_MAX), "SIZE_MAX prompt");
 expect(!gen_request_fits_context(static_cast<size_t>(INT64_MAX)+1,1,INT64_MAX), "before narrowing prompt");
 expect(gen_request_fits_context(1,262135,262144), "max output for one prompt");
 expect(!gen_request_fits_context(1,262136,262144), "max output one beyond");
 expect(!gen_request_fits_context(1,262144,262144), "output equals context");
 expect(gen_request_fits_context(229368,32768,262144), "32K output boundary");
 expect(!gen_request_fits_context(229369,32768,262144), "32K output one beyond");
 expect(gen_request_fits_context(196600,65536,262144), "64K output boundary");
 expect(!gen_request_fits_context(196601,65536,262144), "64K output one beyond");
 expect(gen_request_fits_context(1,INT64_MAX-9,INT64_MAX), "wide artificial context boundary");
 expect(!gen_request_fits_context(1,INT64_MAX-8,INT64_MAX), "wide artificial context one beyond");
 const std::vector<int64_t> contexts={INT64_MIN,-1,0,8,9,10,262144,2147483639,INT64_MAX-1,INT64_MAX};
 const std::vector<long long> outputs={LLONG_MIN,-1,0,1,2,32768,65536,262135,262136,262144,LLONG_MAX-9,LLONG_MAX-8,LLONG_MAX};
 const std::vector<size_t> prompts={0,1,2,196600,196601,229368,229369,262136,static_cast<size_t>(INT64_MAX),static_cast<size_t>(INT64_MAX)+1,SIZE_MAX};
 for (auto c:contexts) for(auto o:outputs) for(auto p:prompts)
   expect(gen_request_fits_context(p,o,c)==oracle(p,o,c),"wide predicate grid");
 for (int64_t c=-3;c<66;++c) for(long long o=-3;o<66;++o) for(size_t p=0;p<66;++p)
   expect(gen_request_fits_context(p,o,c)==oracle(p,o,c),"exhaustive small oracle");
 uint64_t rng=0x43093fa1842512ULL;
 auto draw=[&](){rng ^= rng<<13; rng ^= rng>>7; rng ^= rng<<17; return rng;};
 for(int i=0;i<100000;++i) {
  const size_t p=draw(); long long o=static_cast<long long>(draw() & LLONG_MAX);
  int64_t c=static_cast<int64_t>(draw() & INT64_MAX);
  if(draw()&1)o=-o; if(draw()&1)c=-c;
  expect(gen_request_fits_context(p,o,c)==oracle(p,o,c),"random wide oracle");
 }
 for(const std::string line : {
     "GEN 1 0", "GEN +01 0,1", "GEN   +01 0,1", "GEN \t+1 0,1", "GEN 1,0,1", "GEN 1\t0,1",
     "GEN 1 0 1", "GEN 1 0,,1", "GEN 1 temperature=1 top_p=0.95 top_k=20 seed=12345 aux_cpus=1 1,2",
     "GEN 16 temperature=1 top_p=0.95 top_k=20 seed=12345 aux_cpus=1 ckpt=1 pin=3 1,2,3",
     "GEN 16 temperature=1 top_p=0.95 top_k=20 seed=12345 aux_cpus=1 ckpt=1 pin=9 1,2,3",
     "GEN 1 unknown=retained cvec=0 pipe=0.5 logit_bias=1:2.5 1,2",
     "GENI +1 temperature=1 img_keys=abc,def /not-opened-by-cpu-test 1,2",
     "GEN 262135 1"}) compare_valid(line);
 compare_valid("GEN 1 0",10);
 for(const std::string line:{
     "GEN 0 1","GEN -1 1","GEN -9223372036854775808 1","GEN -9223372036854775809 1",
     "GEN 9223372036854775807 1","GEN 9223372036854775808 1","GEN 99999999999999999999999999999999 1",
     "GEN  1junk","GEN  abc 1","GEN ","GEN + 1","GEN 1 ","GEN 1 -1","GEN 1 2147483648",
     "GEN 1 1junk","GEN 262136 1","GEN 262144 1","GENI 1 /not-opened-by-cpu-test 1,2"}) {
  Result result;
  const int64_t ctx=(line.rfind("GENI",0)==0)?10:262144;
  expect(!candidate::parse(line,ctx,result),"malformed/overbudget packet rejected before setup");
 }
 // Realistic CPU-only list boundaries: at most ~0.5 MiB text; no model or GPU.
 for (const long long output : {32768LL,65536LL}) {
  const size_t limit=static_cast<size_t>(262144-8-output);
  std::string line="GEN "+std::to_string(output)+" ";
  for(size_t i=0;i<limit;++i) { if(i)line+=','; line+='1'; }
  compare_valid(line);
  line+=",1"; Result result;
  expect(!candidate::parse(line,262144,result),"real boundary list one beyond");
 }

 size_t reserved = 123;
 for(size_t cap : {size_t(0),size_t(1),size_t(10),size_t(100),SIZE_MAX})
 for(size_t n : {size_t(0),size_t(1),size_t(10),SIZE_MAX})
 for(long long out : {-1LL,0LL,1LL,10LL,LLONG_MAX})
 for(int w : {-1,0,1,8,INT_MAX}) {
  reserved = 123;
  const bool ok = candidate::gen_request_reserve(n,out,w,cap,reserved);
  if(!ok) expect(reserved == 123,"failed reserve leaves output unchanged");
  const bool oracle_ok = out >= 1 && w >= 0 &&
      (__int128)n + (__int128)out + (__int128)w <= (__int128)cap;
  expect(ok == oracle_ok, "reserve wide subtraction oracle");
  if(ok) expect((__int128)reserved == (__int128)n+out+w, "reserve exact");
 }
 for(const std::string line : {
  "BGEN 0 9223372036854775808 1", "BGEN 9999999999999999999999 1 1",
  "BGEN x 1 1", "BGEN 0 x 1", "BGEN 0 -1 1", "BGEN 0 12 1",
  "BGEN 0 10 1,2,3", "BGENI 0 10 /not-opened 1,2,3",
  "GEN 12 pipe=0.5 1", "GENI 12 /not-opened 1"}) {
  Result r;
  strata::prefill::Prefill::pipe=0.25;
  expect(!candidate::parse(line,20,r,2),"batch/general permanent bad request");
  expect(strata::prefill::Prefill::pipe==0.25,"invalid lengths leave pipe unchanged");
  expect(candidate::parse("BGEN 0 9 1,2",20,r,2),"valid after invalid same process");
  expect(r.max_new==1 && r.ids.size()==2,"batch admission remains one token");
 }
 for(const std::string line : {"BGEN 0 9 1,2,3","BGENI 0 9 /not-opened 1,2,3"}) {
  Result r; expect(candidate::parse(line,20,r,2),"full batch budget boundary inclusive");
  expect(!candidate::parse(line,19,r,2),"full batch budget not rewritten one");
 }


 for(const std::string line : {"GEN 9 1,2,3", "GENI 9 /not-opened 1,2,3"}) {
  Result r;
  expect(candidate::parse(line,20,r),"ordinary full context exact edge");
  expect(!candidate::parse(line,19,r),"ordinary full context one beyond");
 }
 for(const std::string line : {"GEN 1 ", "GEN 1 -1", "GEN 1 2147483648",
                               "GENI 1 /not-opened ", "GENI 1 /not-opened -1",
                               "GENI 9223372036854775808 /not-opened 1"}) {
  Result r;
  expect(candidate::parse("GEN 1 1",20,r),"valid before malformed");
  expect(!candidate::parse(line,20,r),"empty invalid ids or malformed GENI rejected");
  expect(candidate::parse("GEN 1 1",20,r),"valid text after malformed GENI/GEN");
 }

 size_t retained=0;
 for(int i=1;i<argc;++i) {
  std::ifstream in(argv[i]); expect(bool(in),"retained .gen is readable");
  std::string line;
  while(std::getline(in,line)) {
   if(line.empty())continue;
   expect(line.rfind("GEN ",0)==0 || line.rfind("GENI ",0)==0,"retained protocol packet prefix");
   compare_valid(line); ++retained;
  }
 }
 expect(retained==static_cast<size_t>(argc-1),"all supplied retained packets compared");
 std::cout << "PASS checks=" << checks << " retained_packets=" << retained
           << " exact_source_extraction=1 cpu_only=1\n";
}
'''
cpp=head+wrapper('baseline',b,old_guard)+wrapper('candidate',s)+tests
(T/'test_gen_request_bounds.cpp').write_text(cpp)
requests=args.retained
assert all(p.is_file() for p in requests)
(T/'retained-private-request-manifest.json').write_text(json.dumps([{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in requests],indent=2)+'\n')
results=[]
for name,flags in [('normal',['-O2']),('ubsan',['-O1','-g','-fsanitize=undefined','-fno-sanitize-recover=all'])]:
 binary=T/f'test-gen-request-bounds-{name}'
 command=['/usr/bin/g++','-std=c++20','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']+flags+['-I'+str(ROOT/'include'),str(T/'test_gen_request_bounds.cpp'),'-o',str(binary)]
 t=time.time();compiled=subprocess.run(command,capture_output=True,text=True,timeout=90)
 (T/f'{name}-compile.log').write_text(compiled.stdout+compiled.stderr)
 row={'name':name,'compile_command':command,'compile_returncode':compiled.returncode,'compile_seconds':time.time()-t}
 if compiled.returncode:
  results.append(row); print(compiled.stderr); break
 env=os.environ.copy();env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
 t=time.time();run=subprocess.run([str(binary)]+[str(p) for p in requests],capture_output=True,text=True,env=env,timeout=90)
 (T/f'{name}-run.log').write_text(run.stdout+run.stderr)
 row.update(run_returncode=run.returncode,run_seconds=time.time()-t,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),summary=run.stdout.splitlines()[-1:] if run.stdout else [],ubsan_stderr_empty=not run.stderr)
 results.append(row)
 print(json.dumps(row))
 if run.returncode: print(run.stdout[-8000:]+run.stderr[-8000:]);break
(T/'results.json').write_text(json.dumps(results,indent=2)+'\n')

if len(results)==2 and all(x.get('run_returncode')==0 for x in results):
 probes=[
  ("budget-overflow",["BGEN 0 9223372036854775808 1"],False,False),
  ("slot-overflow",["BGEN 9999999999999999999999 1 1"],False,False),
  ("slot-no-digit",["BGEN x 1 1"],False,False),
  ("full-budget",["BGEN 0 10 1,2,3"],False,False),
  ("geni-full-budget",["BGENI 0 10 /not-opened 1,2,3"],False,False),
  ("unavailable-slot",["BGEN 9 1 1"],True,False),
  ("occupied-slot",["BGEN 0 1 1"],True,True),
  ("recovery",["GEN 9223372036854775808 1","GEN 1 1"],False,False),
  ("recovery-geni",["GENI 9223372036854775808 /not-opened 1","GEN 1 1"],False,False)]
 receipts=[]
 for variant in ["normal","ubsan"]:
  for name,packets,retryable,occupied in probes:
   env=os.environ.copy()
   if occupied: env["OCCUPIED"]="1"
   run=subprocess.run([str(T/f"test-gen-request-bounds-{variant}"),"--probe"]+packets,
                      capture_output=True,text=True,env=env,timeout=30)
   assert run.returncode==0 and not run.stderr,(name,run.stderr)
   errors=[line for line in run.stdout.splitlines() if line.startswith("ERR ")]
   assert len(errors)==1 and errors[0].startswith("ERR BGEN:")==retryable,(name,run.stdout)
   assert "DONE" not in run.stdout
   if name.startswith("recovery"):
    assert "PROBE accepted=0" in run.stdout and "PROBE accepted=1 max_new=1 ids=1" in run.stdout
   receipts.append({"variant":variant,"name":name,"stdout":run.stdout,"retryable":retryable})
 (T/"protocol-harness-probes.json").write_text(json.dumps(receipts,indent=2)+"\n")
 print("PASS parser-harness protocol probes=",len(receipts))
sys.exit(0 if len(results)==2 and all(x.get('run_returncode')==0 for x in results) else 1)
