from pathlib import Path
import subprocess,json,queue,threading,time,uuid,fcntl,hashlib,sys
R=Path('/home/radneon/strata/rnd-next-20261017');mode=sys.argv[1];assert mode in ('smoke','abba64','final64','long200k','short8k')
OUT=R/'hc-j48-prefill-normal-v1-tests'/mode;OUT.mkdir(parents=True,exist_ok=False)
root=R/('hc-j48-heldout-capture-v1-validation8k' if mode in ('smoke','short8k') else 'hc-j48-heldout-capture-v1-validation64k')
req=json.loads((root/'requests.json').read_text())[0];ids=req['ids'];count=req['output_count']
ref=[int(x.split()[1]) for x in (root/'qualified/session.stdout').read_text().splitlines() if x.startswith('T ')];assert len(ref)==count
if mode=='long200k':
 root=R/'hc-final0705-long200k-B';ids=json.loads((root/'prompt-200000.json').read_text());count=256;ref=[int(x.split()[1]) for x in (root/'diagnostic.stdout').read_text().splitlines() if x.startswith('T ')];assert len(ref)==count

template=json.loads((R/'hc-j48-heldout-capture-v1-validation8k/qualified/session.receipt.json').read_text())['command']
def call(a):return subprocess.run(a,check=True,capture_output=True,text=True)
def one(label,arm):
 d=OUT/label;d.mkdir();token=uuid.uuid4().hex;a=(json.loads((R/'hc-final-bundle-benchmark64k-v2'/('01A.receipt.json' if arm=='base' else '01B.receipt.json')).read_text())['command'] if mode=='final64' else template[:]);a[1]='create';a=[x for x in a if x not in ('--rm','--pull=never')]
 a[a.index('--name')+1]='strata-j48-normal-'+token[:12];a[a.index('--label')+1]='strata.rnd.token='+token
 for name in ['STRATA_PIPELINE_DEBUG','STRATA_DECODE_TIMING']:
  for i in range(len(a)-1,-1,-1):
   if a[i].startswith(name+'=') and i>0 and a[i-1]=='-e':del a[i-1:i+1]
 if arm!='base':a[a.index('/next/hc-shape-aware-v1-build/strata')]='/next/hc-j48-prefill-normal-v1-build/strata'
 if arm=='on':
  i=a.index('STRATA_GFX906_PREFILL_J48') if 'STRATA_GFX906_PREFILL_J48' in a else -1
  if i>=0:assert a[i-1]=='-u';del a[i-1:i+1]
  i=next(i for i,x in enumerate(a) if x.startswith('sha256:'));a[i:i]=['-e','STRATA_GFX906_PREFILL_J48=1']
 (d/'command.json').write_text(json.dumps(a,indent=2));cid=call(a).stdout.strip();assert len(cid)==64
 def inspect():
  x=json.loads(call(['docker','inspect',cid]).stdout)[0];assert x['Id']==cid and x['Config']['Labels'].get('strata.rnd.token')==token;return x
 inspect();q=queue.Queue();tokens=[];done=None;p=None
 with (d/'stderr.log').open('wb') as err,(d/'stdout.log').open('w') as log:
  try:
   p=subprocess.Popen(['docker','start','-a','-i',cid],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
   def reader():
    for line in p.stdout:q.put(line)
    q.put(None)
   t=threading.Thread(target=reader,daemon=True);t.start();deadline=time.monotonic()+1200;sent=False;info=None
   while True:
    if time.monotonic()>deadline:raise TimeoutError('model deadline')
    line=q.get(timeout=max(1,deadline-time.monotonic()))
    if line is None:break
    log.write(line);log.flush()
    if line.startswith('INFO '):
     info=dict(x.split('=',1) for x in line.split()[1:] if '=' in x);assert info.get('expert_slots')=='18018' and info.get('expert_slots_primary')=='9399'
    if line.startswith('READY ') and not sent:
     assert info
     free={str(c):int((c/'mem_info_vram_total').read_text())-int((c/'mem_info_vram_used').read_text()) for c in [Path('/sys/class/drm/card1/device'),Path('/sys/class/drm/card2/device')]};(d/'ready-vram.json').write_text(json.dumps(free));assert min(free.values())>=768*1024**2
     p.stdin.write('GEN '+str(count)+' temperature=0 top_p=1 top_k=1 seed=12345 '+','.join(map(str,ids))+chr(10));p.stdin.flush();sent=True
    elif line.startswith('T '):tokens.append(int(line.split()[1]))
    elif line.startswith('DONE '):done=line.strip();p.stdin.write('QUIT'+chr(10));p.stdin.flush();p.stdin.close()
   p.wait(timeout=60);t.join(timeout=5);assert not t.is_alive();x=inspect();(d/'inspect.json').write_text(json.dumps(x,indent=2))
   assert p.returncode==0 and x['State']['ExitCode']==0 and x['State']['Status']=='exited'
   (d/'tokens.json').write_text(json.dumps(tokens));assert done and tokens==ref,'token mismatch';v=done.split();assert int(v[1])==count and int(v[2])==len(ids)
   result=dict(arm=arm,pp_ms=float(v[3]),tg_ms=float(v[4]),pp_tps=len(ids)*1000/float(v[3]),tg_tps=count*1000/float(v[4]),same_tokens=True,done=done);(d/'result.json').write_text(json.dumps(result,indent=2))
  finally:
   x=inspect()
   if x['State']['Running']:call(['docker','stop','--time','10',cid])
   if p is not None and p.poll() is None:p.wait(timeout=30)
   call(['docker','rm',cid]);assert not call(['docker','ps','-a','--filter','id='+cid,'--format','{{.ID}}']).stdout.strip()
 return result
with Path('/home/radneon/strata/combined-gfx906-20261017/benchmark.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not call(['docker','ps','-q']).stdout.strip()
 b=json.loads((R/'hc-j48-prefill-normal-v1-assets/status.json').read_text());assert b['phase']=='complete';assert hashlib.sha256((R/'hc-j48-prefill-normal-v1-build/strata').read_bytes()).hexdigest()==b['binary_sha256']
 results=[]
 try:
  for i,arm in enumerate(['on','off','off','on'] if mode=='short8k' else ['base','off','on'] if mode=='smoke' else (['base','on','on','base','on','base','base','on','base','on','on','base'] if mode=='final64' else (['base','on'] if mode=='long200k' else ['base','on','on','base']))):
   results.append(one(str(i+1)+'-'+arm,arm));(OUT/'results.json').write_text(json.dumps(results,indent=2))
  (OUT/'status.json').write_text(json.dumps(dict(state='complete',results=results),indent=2))
 except BaseException as e:
  (OUT/'status.json').write_text(json.dumps(dict(state='failed',error=repr(e),results=results),indent=2));raise
