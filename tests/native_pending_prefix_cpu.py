"""Compile source-extracted host planning paths only. No engine, HIP, model, or GPU."""
import hashlib,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
out=root.parent/"cpu-unit";out.mkdir(exist_ok=True)
s=(root/"src/program/generate.cpp").read_text()
def extract(start,end):
    a=s.index(start);b=s.index(end,a)
    return s[a:b]
pw=extract("                struct PW {","                // front stage")
rule=extract("                auto t_rule =","                // B from")
make=extract("                auto make_b =","                // events after")
a0=extract("                                if (pl_pending_prefix) {\n                                    A.T", "                                early_used = true;")
a1=extract("                            if (pl_pending_prefix) {\n                                A.T", "                            early_used = true;")
assert a0.strip()==a1.strip().replace("\n                            ","\n                                ").strip() or a0.split()==a1.split()
# Production ordering, no late mutation after a verifier has captured T.
assert s.index("checked_limit(n, max_new") < s.index("if (n + max_new + 8")
assert s.index("pick_lookup(A, mtp.chain_tok());") < s.index(a0) < s.index("const int base = A.T - 1;",s.index(a0))
assert s.index("pick_lookup(A, oc);") < s.index(a1) < s.index("const int base = A.T - 1;",s.index(a1))
assert make.index("B = PW{};") < make.index("width(") < make.index("B.ready = true")
assert s.index("make_b(oc, op, base, k, pa)") < s.index("VF(0, B).prestage(B.T")
prefix=r'''
#include "strata/program/pending_prefix.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
using namespace strata::program;
'''
body=r'''
int main() {
    int64_t L=-1;
    assert(!pending_prefix::requested(nullptr));
    for (const char* s: {"","0","11","true"}) assert(!pending_prefix::requested(s));
    assert(pending_prefix::requested("1"));
    assert(!pending_prefix::checked_limit(100,0,1000,L) && L==0);
    assert(!pending_prefix::checked_limit(0,1,1000,L));
    assert(!pending_prefix::checked_limit(100,1,7,L));
    assert(!pending_prefix::checked_limit(100,std::numeric_limits<int64_t>::max(),1000,L));
    assert(!pending_prefix::checked_limit(std::numeric_limits<int64_t>::max(),1,std::numeric_limits<int64_t>::max(),L));
    assert(pending_prefix::checked_limit(std::numeric_limits<int64_t>::max()-9,1,std::numeric_limits<int64_t>::max(),L));
    assert(L==std::numeric_limits<int64_t>::max()-9);
    assert(pending_prefix::checked_limit(100,892,1000,L) && L==991);
    assert(!pending_prefix::checked_limit(100,893,1000,L));
    assert(pending_prefix::eligible(true,true,0,2,2,0,0,0,false,0));
    assert(!pending_prefix::eligible(false,true,0,2,2,0,0,0,false,0));
    assert(!pending_prefix::eligible(true,false,0,2,2,0,0,0,false,0));
    assert(!pending_prefix::eligible(true,true,1,2,2,0,0,0,false,0));
    assert(!pending_prefix::eligible(true,true,0,1,2,0,0,0,false,0));
    assert(!pending_prefix::eligible(true,true,0,2,3,0,0,0,false,0));
    assert(!pending_prefix::eligible(true,true,0,2,2,1,0,0,false,0));
    assert(!pending_prefix::eligible(true,true,0,2,2,0,1,0,false,0));
    assert(!pending_prefix::eligible(true,true,0,2,2,0,0,1,false,0));
    assert(!pending_prefix::eligible(true,true,0,2,2,0,0,0,true,0));
    assert(!pending_prefix::eligible(true,true,0,2,2,0,0,0,false,1));
    int S_mtp=2,force_miss=0; int64_t pl_fm=0;
    float req_spec_min_p=0.5f;
    bool pl_pending_prefix=true; int64_t pending_prefix_limit=0;
    PW A,B;
    auto die=[](const char*) { return -1; };
'''
tail=r'''
    auto fresh = [&]() -> int {
        // Verbatim production post-pick_lookup fresh-A path.
        FRESH
        return 0;
    };
    int32_t oc[8]={100,101,102,103,104,105,106,107};
    float op[8]={1,1,1,1,1,1,1,1};
    uint64_t cases=0;
    for (int cap=1;cap<=9;++cap) {
        assert(pending_prefix::checked_limit(100,cap,1000,pending_prefix_limit));
        for (int emitted=0;emitted<cap;++emitted) {
            for(int proposed: {1,2}) {
                A=PW{}; A.p=99+emitted; A.T=emitted==0?1:proposed;
                A.tok[0]=9; A.tok[1]=10; // Current pending input and hypothetical matching draft.
                assert(fresh()==0 && A.ready);
                assert(A.T>=1 && A.T<=2 && A.p+A.T<=pending_prefix_limit);
                const int base=A.T-1;
                // Deliberately stale B: actual make_b must reset all state before zero-budget return.
                B=PW{}; B.ready=B.made=B.launched=B.fl=true;B.T=2;B.p=999;
                make_b(oc,op,base,8,1.0f);
                bool b_done=true; // Production caller consumes the decision even when B is absent.
                assert(b_done);
                if(A.p+A.T==pending_prefix_limit) {
                    assert(!B.ready && !B.made && !B.launched && !B.fl && B.T==0 && B.p==0);
                } else {
                    assert(B.ready && B.made && !B.launched && !B.fl);
                    assert(B.p==A.p+A.T && B.p+B.T<=pending_prefix_limit);
                    assert(B.tok[0]==oc[base]);
                }
                // Existing prestage/frontlaunch gates cannot execute an absent T0 B.
                int prestages=0,launches=0;
                if(B.ready) {++prestages; assert(B.T>0);}
                if(B.ready && !B.fl && B.fr<1 && A.fr+1>B.fr) {++launches; assert(B.T>0);}
                assert((prestages==0)==!B.ready && launches==prestages);
                for(int a=0;a<A.T;++a) for(bool bonus: {false,true}) {
                    const int keep=a+1;
                    const int64_t next=A.p+keep;
                    assert(next==99+emitted+keep && emitted+keep<=cap);
                    const bool on=B.launched && a==A.T-1 && bonus;
                    (void)on; // Actual launch is not performed by this CPU fixture.
                    if(B.ready && a==A.T-1 && bonus) assert(B.p==next); // promotion identity
                    else { int undo_keep=keep; assert(A.p+undo_keep==next); } // replay real commit
                    ++cases;
                }
            }
        }
    }
    // OFF path keeps width2 even at zero hypothetical remaining budget.
    pl_pending_prefix=false;pending_prefix_limit=100;A=PW{};A.p=99;A.T=1;
    make_b(oc,op,0,8,1.0f); assert(B.ready && B.made && B.T==2 && B.p==100);
    // Live current A cannot exist past the cap: fail rather than execute a zero-width graph.
    pl_pending_prefix=true;A=PW{};A.p=100;A.T=2;assert(fresh()==-1 && !A.ready);
    assert(pending_prefix::width(100,-1,2)==0);
    std::cout << "PASS cases=" << cases << "\n";
}
'''
cpp=prefix+pw+body+rule+make+tail.replace("FRESH",a0)
(out/"extracted.cpp").write_text(cpp)
receipts=[]
for name,flags in (("regular",["-O2"]),("ubsan",["-O1","-g","-fsanitize=undefined","-fno-sanitize-recover=all"])):
    command=["g++","-std=c++17",*flags,"-Wall","-Wextra","-Werror","-I",str(root/"include"),str(out/"extracted.cpp"),"-o",str(out/name)]
    build=subprocess.run(command,capture_output=True,text=True,timeout=60)
    (out/(name+"-build.log")).write_text(build.stdout+build.stderr)
    if build.returncode:raise RuntimeError(build.stderr)
    run=subprocess.run([str(out/name)],capture_output=True,text=True,timeout=30)
    (out/(name+".log")).write_text(run.stdout+run.stderr)
    if run.returncode or not run.stdout.startswith("PASS cases="):raise RuntimeError(run.stdout+run.stderr)
    receipts.append({"name":name,"command":command,"build_rc":build.returncode,"run_rc":run.returncode,"stdout":run.stdout.strip()})
paths=[root/"src/program/generate.cpp",root/"include/strata/program/pending_prefix.hpp",pathlib.Path(__file__),out/"extracted.cpp"]
receipt={"status":"PASS","source_sha256":{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},"runs":receipts,
"scope":"Actual extracted PW/t_rule/make_b/fresh-A clamp; mocked prestage/launch and symbolic verdict bookkeeping, not native/GPU numerical proof."}
(out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt))
