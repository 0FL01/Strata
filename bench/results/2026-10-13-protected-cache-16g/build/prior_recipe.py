#!/usr/bin/env python3
"""Two exact host baseline reproductions, then two peer-affinity TUs; reused qualified HIP object. No GPU execution."""
import argparse,hashlib,json,os,shlex,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
IMAGE='sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646'
PINS={'CMakeFiles/strata.dir/src/program/generate.cpp.o': '605e2b5290b66aa4f899c1f602c61f1b88ff53ad96bacb76bb4264faba0fe485', 'libstrata_engine.a': '6999f03f57473776a99b72bf4ebe8766a9c6c751f74affd010a2fccf36412da9', 'libstrata_prefill.a': '56f94c06db6f505212fb74a5057e9fed77a651ae7279b810c18a90da3c2375ef', 'libstrata_spec.a': '52b87c781c881a52880886d3598337a877d4a61051911f6a5f5ad93588e174b2', 'libstrata_kernels.a': '135bfd9e51c94d9596db56d69db956f0397ff088097b28950002b98c3b97af9b', 'libstrata_core.a': '0a445cccbca385adcd0da1b15b7e4bb8e3bd4b7d2aa2de308becfb05d37871af', 'libstrata_kernels_cpu.a': '30579ab20c14b8cd9d8fa70a7c3eb7d2fefc9e214fa7ad4cc1c4787f8c80de8a', 'ggml/src/libggml-cpu.a': 'a9fc4bf801bb7143635f78337062abb20b67849d7f43b531d1c91604cee28c0f', 'libstrata_mmq.a': '53bbd154dd4978422993c2e65eed982cfcac38278a82c88df6bc97fae5a56c10', 'ggml/src/libggml-base.a': 'bae60befac1bde1706241a530bd256eccf7552d2ba1c9dc260ac3eda750c9951', 'CMakeFiles/strata_prefill.dir/src/prefill/prefill.cpp.o': 'efff91107cf3339e5929ac510097168da5c51d64012a93ece3894aa64b5d215d', 'CMakeFiles/strata_prefill.dir/flags.make': '35d3ef4654d9564a530469de435eac320dde285a843aaddc1f6b4c8f388056e2', 'CMakeFiles/strata_prefill.dir/build.make': '12d39d3ca3c7e6035c422b971b179cd0c4d34d057e7087a0cfe18f1bab825f1d', 'CMakeFiles/strata.dir/link.txt': 'cdfd624b73f4ad51a214dd6e73a06b2c1ab08df63fafb229647e0a4beaa873af'}
DEFINES=['-DSTRATA_HIP_GFX906=1', '-DSTRATA_NATIVE_EXPERTS=1', '-DSTRATA_PREFILL_FUSED=1', '-DSTRATA_PREFILL_MMQ=1', '-DSTRATA_VERSION="0.1.40"', '-DUSE_PROF_API=1', '-D__HIP_PLATFORM_AMD__=1']
BASE_BINARY='c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049'
LINK=shlex.split('/opt/rocm/lib/llvm/bin/clang++ -O3 -DNDEBUG --offload-arch=gfx906 CMakeFiles/strata.dir/src/program/generate.cpp.o -o strata libstrata_engine.a libstrata_prefill.a libstrata_spec.a libstrata_engine.a libstrata_kernels.a libstrata_core.a libstrata_kernels_cpu.a ggml/src/libggml-cpu.a /opt/rocm/core-7.14/lib/libhipblas.so.3.5 libstrata_mmq.a /opt/rocm/lib/libamdhip64.so.7.14.60850-0000000 /opt/rocm/core-7.14/lib/llvm/lib/clang/23/lib/linux/libclang_rt.builtins-x86_64.a /opt/rocm/lib/libamdhip64.so.7.14.60850-0000000 ggml/src/libggml-base.a -lm')
IMAGE_INPUTS={'/opt/rocm/core-7.14/lib/libhipblas.so.3.5':'b1c01171fa9cd242d4d534f01bb35c66b0f5376fb909a6f91fe739373b2df2d1','/opt/rocm/lib/libamdhip64.so.7.14.60850-0000000':'fd42fcb591d673976640e676f52bc843ce560a6b7424285fcb85b9f9cd277419','/opt/rocm/core-7.14/lib/llvm/lib/clang/23/lib/linux/libclang_rt.builtins-x86_64.a':'3bf0fdbfdf5442a5d46807f3e1d1b380575fd0dabad867dd97fb42515ba50f65'}
BASE_SOURCES={'generate':'e7a5a754af2155c779aad5f2232ba1c0052ebbd2a4795d40885eff571b62221c','prefill':'db66a66d96420bac3303cc27a984b16eaec5583b02823042f2798771e825d8bc'}
SOURCES={'generate':'src/program/generate.cpp','prefill':'src/prefill/prefill.cpp'}
OBJECTS={'generate':'CMakeFiles/strata.dir/src/program/generate.cpp.o','prefill':'CMakeFiles/strata_prefill.dir/src/prefill/prefill.cpp.o'}
HEADERS={'include/strata/core/verify.hpp':'5a959164cbaed0feee14463ea036c0002816993a21b2f987d6dc57566fceef13','include/strata/kernels/iq_kernels.hpp':'00e41a0b6d841cf6c532e012b113f5f0e4e9aa6b9e0d59a077b0e0bce2f1897a'}
QUALIFIED_BASE_BINARY='ba130bd3742f3f1d53cf0c65f38732400f2ceed4f5d78038aa0f84783d5bc863'
REUSED={'libstrata_prefill.a':'cd3d7687b4ff4fd743d2a5800c96ba6b53e3b2dbc0be46d54a2b9f0ddadf0c67','hc_bf16_n4.o':'3e0b616ef7d8658a61dc26cbd6219e1ebd3233ab8afc1a34fe7b23e226bc7b68'}
RECIPES={'CMakeFiles/strata.dir/flags.make':'ddd9263593ff80b58ae5db96a9718ede79daa89c5d5392f0e2434e3545ddf6e8','CMakeFiles/strata.dir/build.make':'6304b4a9bb0f0786367aecab701d0ca9c0eb09aa0934ec44a41d1cdacce3345d','CMakeFiles/strata_prefill.dir/flags.make':PINS['CMakeFiles/strata_prefill.dir/flags.make'],'CMakeFiles/strata_prefill.dir/build.make':PINS['CMakeFiles/strata_prefill.dir/build.make']}
def need(ok,label):
 if not ok:raise RuntimeError(label)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def info(p):
 p=Path(p);need(p.is_file() and not p.is_symlink(),'regular '+str(p));return dict(sha256=sha(p),bytes=p.stat().st_size)
def checked(root,pins):
 result={n:info(Path(root)/n) for n in pins}
 for n,h in pins.items():need(result[n]['sha256']==h,'pinned input '+n)
 return result
def check_inputs(root):return checked(root,PINS)
def command(tu):
 need(tu in SOURCES,'fixed TU');defs=DEFINES
 inc=['-I/src/include','-I/src/third_party/llama.cpp/ggml/src/../include','-isystem','/src/include/strata/platform/hip_compat','-isystem','/opt/rocm/include']
 inc+=['-isystem','/opt/rocm/core-7.14/include']
 obj=OBJECTS[tu]
 return ['/opt/rocm/llvm/bin/clang++']+defs+inc+['-O3','-DNDEBUG','-std=c++20','-Wall','-Wextra','-MD','-MT',obj,'-MF',obj+'.d','-o',obj,'-c','/src/'+SOURCES[tu]]
def link_command(out):return LINK[:1]+['--hip-link',str(out/'hc_bf16_n4.o')]+LINK[1:]+['-Wl,-Map,'+str(out/'link.map'),'-Wl,--cref']
def integration_symbols(text):
 need('Cross Reference Table' in text,'link cross-reference');table=text.split('Cross Reference Table',1)[1];out={}
 for n in ('strata_hc_bf16_n4_supported','strata_hc_bf16_n4_launch','strata_peer_affinity_capture','strata_peer_affinity_pinned','strata_peer_affinity_begin','strata_peer_affinity_end','strata_peer_affinity_report'):
  rows=[l.split() for l in table.splitlines() if l.startswith(n+' ')];owner='/out/build/hc_bf16_n4.o' if n.startswith('strata_hc_') else 'libstrata_prefill.a(prefill.cpp.o)'
  need(len(rows)==1 and rows[0][1]==owner,'exact symbol owner '+n);out[n]=owner
 for prefix,owner in [('strata::prefill::Gemm::bf16(','libstrata_prefill.a(gemm.cu.o)'),('strata::core::Verifier::run(','libstrata_engine.a(verify.cpp.o)')]:
  rows=[l for l in table.splitlines() if l.startswith(prefix)];need(len(rows)==1 and rows[0].rstrip().endswith(owner),'original member owner '+prefix);out[prefix]=owner
 return out
def check_recipe():
 result={}
 for n,h in RECIPES.items():
  root='/closure' if 'strata_prefill.dir' in n else '/recipes';result[n]=info(Path(root)/n);need(result[n]['sha256']==h,'recipe '+n)
 for tu in SOURCES:
  target='strata' if tu=='generate' else 'strata_prefill';base=Path('/recipes/CMakeFiles' if tu=='generate' else '/closure/CMakeFiles')/(target+'.dir');flags={}
  for line in (base/'flags.make').read_text().splitlines():
   if ' = ' in line:
    k,v=line.split(' = ',1)
    if k.startswith('CXX_'):need(k not in flags,'duplicate flags');flags[k]=shlex.split(v)
  cmd=command(tu);ix=cmd.index('-I/src/include');end=cmd.index('-O3')
  need(flags==dict(CXX_DEFINES=cmd[1:ix],CXX_INCLUDES=cmd[ix:end],CXX_FLAGS=cmd[end:end+5]),'recorded recipe flags '+tu)
  matches=[' '.join(x.split()) for x in (base/'build.make').read_text().splitlines() if x.strip().startswith('/opt/rocm/') and x.rstrip().endswith('-c /src/'+SOURCES[tu])]
  need(matches==[' '.join([cmd[0],'$(CXX_DEFINES)','$(CXX_INCLUDES)','$(CXX_FLAGS)']+cmd[cmd.index('-MD'):])],'recorded compile recipe '+tu)
 need(shlex.split(Path('/closure/CMakeFiles/strata.dir/link.txt').read_text())==LINK,'retained link recipe');return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest-sha',required=True);a=ap.parse_args();need(not Path('/dev/kfd').exists() and not Path('/dev/dri').exists(),'no GPU devices');need(sha(HERE/'SHA256SUMS')==a.manifest_sha,'core manifest');package={}
 for line in (HERE/'SHA256SUMS').read_text().splitlines():
  h,n=line.split('  ',1);p=Path(n);need(not p.is_absolute() and '..' not in p.parts and n not in package,'safe manifest');package[n]=info(HERE/p);need(package[n]['sha256']==h,'package '+n)
 need(set(package)=={str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS'},'exact package')
 build=Path('/src/build-906');out=Path('/out/build');need((build.stat().st_dev,build.stat().st_ino)==(out.stat().st_dev,out.stat().st_ino),'build overlay')
 original=check_inputs('/closure');need(check_inputs(build)==original,'fresh closure');need(sha('/closure/strata')==BASE_BINARY,'original c183 binary')
 reused=checked('/qualified',REUSED);need(sha('/qualified/strata')==QUALIFIED_BASE_BINARY,'clean qualified N4 binary');recipes=check_recipe();image_inputs={p:sha(p) for p in IMAGE_INPUTS};need(image_inputs==IMAGE_INPUTS,'image link inputs')
 checkout={n:info(Path('/original')/n) for n in SOURCES.values()}
 for tu,n in SOURCES.items():need(sha(Path('/src')/n)==sha(HERE/(tu+'.cpp.baseline'))==BASE_SOURCES[tu],'compiled c183 source '+tu)
 checked('/src',HEADERS)
 receipt=dict(passed=False,image=IMAGE,package_manifest_sha256=a.manifest_sha,package=package,host_translation_units_compiled=0,gpu_kernel_translation_units_compiled=0,engine_gpu_kernels_recompiled=False,gpu_execution=False,original_inputs_before=original,reused_inputs_before=reused,checkout_sources_before=checkout,recipe_inputs=recipes,image_inputs=image_inputs,compile_argv={t:command(t) for t in SOURCES},link_argv=link_command(out),baseline_binary_sha256=BASE_BINARY,qualified_baseline_binary_sha256=QUALIFIED_BASE_BINARY,baseline_source_sha256=BASE_SOURCES,header_sha256=HEADERS,steps=[])
 def save():(out/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 def run(name,argv,timeout=300):
  (out/(name+'-argv.json')).write_text(json.dumps(argv)+'\n');start=time.monotonic()
  with (out/(name+'.log')).open('xb') as f:q=subprocess.run(argv,cwd=build,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  receipt['steps'].append(dict(name=name,argv=argv,returncode=q.returncode,seconds=time.monotonic()-start));save();need(q.returncode==0,name+' failed')
 def members(phase):
  ar='/opt/rocm/llvm/bin/llvm-ar';q=subprocess.run([ar,'t','libstrata_prefill.a'],cwd=build,capture_output=True,text=True,check=True,timeout=30);names=q.stdout.splitlines();need(len(names)==len(set(names)) and names.count('prefill.cpp.o')==1,'unique qualified prefill archive member');rows=[]
  for n in names:
   need(n and '/' not in n and n not in ('.','..'),'safe member');q=subprocess.run([ar,'p','libstrata_prefill.a',n],cwd=build,capture_output=True,check=True,timeout=30);rows.append(dict(name=n,sha256=hashlib.sha256(q.stdout).hexdigest(),bytes=len(q.stdout)))
  receipt[phase+'_members']=rows;save();return rows
 save()
 try:
  import shutil
  for n,row in reused.items():shutil.copyfile(Path('/qualified')/n,build/n);need(info(build/n)==row,'qualified input '+n)
  before=members('before');base_objects={'generate':PINS[OBJECTS['generate']],'prefill':next(x['sha256'] for x in before if x['name']=='prefill.cpp.o')};need(base_objects['prefill']=='d8a958cf185323214ef5c0ba42f423681656679e70b0fc9420262eece727035a','qualified prefill object pin');receipt['baseline_object_sha256']=base_objects
  for tu in SOURCES:
   (build/OBJECTS[tu]).parent.mkdir(parents=True,exist_ok=True);run('baseline-'+tu+'-compile',command(tu));receipt['host_translation_units_compiled']+=1;h=sha(build/OBJECTS[tu]);receipt['baseline_'+tu+'_object_sha256']=h;receipt['baseline_'+tu+'_object_reproduced']=h==base_objects[tu];save();need(h==base_objects[tu],'baseline '+tu+' did not reproduce; observer forbidden')
  for tu in SOURCES:
   (Path('/src')/SOURCES[tu]).write_bytes((HERE/(tu+'.cpp.observer')).read_bytes());run('observer-'+tu+'-compile',command(tu));receipt['host_translation_units_compiled']+=1;receipt['observer_'+tu+'_object']=info(build/OBJECTS[tu]);need(receipt['observer_'+tu+'_object']['sha256']!=base_objects[tu],'observer object unchanged')
  run('archive-replace',['/opt/rocm/llvm/bin/llvm-ar','r','libstrata_prefill.a',OBJECTS['prefill']],30);after=members('after');need([x['name'] for x in before]==[x['name'] for x in after],'same member order')
  for x,y in zip(before,after):need(y==dict(name='prefill.cpp.o',**receipt['observer_prefill_object']) if x['name']=='prefill.cpp.o' else x==y,'only qualified prefill member changed')
  receipt['only_prefill_archive_member_replaced']=True
  for n,row in original.items():need(n in {OBJECTS['generate'],OBJECTS['prefill'],'libstrata_prefill.a'} or info(build/n)==row,'unrelated closure changed '+n)
  need(info(build/'hc_bf16_n4.o')==reused['hc_bf16_n4.o'],'qualified HIP object retained')
  receipt['qualified_component_reused']=True;receipt['observer_prefill_archive']=info(build/'libstrata_prefill.a');run('link',link_command(out),180);receipt['disposable_binary_relinked']=True;receipt['artifacts']={n:info(build/n) for n in ('strata','hc_bf16_n4.o','link.map')};receipt['symbol_ownership']=integration_symbols((out/'link.map').read_text())
  from inspect_device import inspect
  receipt['linked_device_image']=inspect(out)
  for n in ('device-inspection.json','hc_bf16_n4_main.isa.txt','hc_bf16_n4_post.isa.txt'):receipt['artifacts'][n]=info(out/n)
 finally:
  receipt['original_inputs_after']=check_inputs('/closure');receipt['reused_inputs_after']=checked('/qualified',REUSED);receipt['checkout_sources_after']={n:info(Path('/original')/n) for n in SOURCES.values()};receipt['original_inputs_unchanged']=receipt['original_inputs_after']==original and sha('/closure/strata')==BASE_BINARY and receipt['checkout_sources_after']==checkout;receipt['reused_inputs_unchanged']=receipt['reused_inputs_after']==reused;receipt['unchanged_package']=all(info(HERE/n)==v for n,v in package.items())
  gates=('disposable_binary_relinked','original_inputs_unchanged','reused_inputs_unchanged','unchanged_package','baseline_generate_object_reproduced','baseline_prefill_object_reproduced','only_prefill_archive_member_replaced','qualified_component_reused');receipt['passed']=all(receipt.get(k) is True for k in gates) and receipt.get('linked_device_image',{}).get('passed') is True;save()
 need(receipt['passed'],'build gates');print(json.dumps(dict(passed=True,binary=receipt['artifacts']['strata'])))
if __name__=='__main__':main()
