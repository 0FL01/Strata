#!/usr/bin/env python3
"""Protocol/fixture/accounting tests; intentionally no GPU or network."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('replay', HERE / 'replay.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
seed = json.loads((HERE / 'prompt-65536.ids.json').read_text())
f = r.Fixture(seed)
rows = []
previous = None
for i in range(13):
    name, ids, n = f.next()
    if name == 'long117173':
        assert len(ids) == 117173 and ids[117170] == r.TURN
    if name.startswith('short'):
        assert ids[:len(previous)] == previous
    if name == 'compact117131':
        assert r.common_prefix(ids, previous) == 117131
    if name == 'decode_cross131072':
        assert len(ids) == 130900 and n == 512
    if name == 'decode_rewrite131100':
        assert r.common_prefix(ids, previous) == 131100
    tokens = [42] * (8 if name == 'cancel_decode' else n)
    f.finish(tokens)
    previous = ids + tokens
    rows.append(dict(case=name, reused=131074 if name == 'decode_rewrite131100' else 100786))
assert f.next() is None
assert len(rows) == 13

def meter(req, total=1024, reserved=64, high=2048):
    return f'[protected-cache] req={req} event=request_complete owned={total-reserved} total={total} reserved={reserved} high_water={high} limit={r.CAP} coverage=complete\n'

valid = ''.join(meter(i) for i in range(1,14)) + '[protected-cache] req=9 event=captured len=131074 target=131072 source=decode bytes=512 owned=1024 total=1024 reserved=0 high_water=2048 limit=17179869184 coverage=complete ms=0.5\n'
assert r.protected_evidence(valid, rows, True)['maximum_accounted_bytes'] == 1024
# total includes reserved; adding reserved a second time would incorrectly reject this.
assert r.protected_evidence(meter(1,r.CAP,64,r.CAP), [], False)['maximum_accounted_bytes'] == r.CAP
for invalid in (valid + meter(13,r.CAP+1,0,r.CAP+1), valid.replace('req=1 ', 'req=0 ',1), valid.replace('coverage=complete','coverage=degraded',1), valid.replace('len=131074','len=131120'), valid + 'strata serve: protected cache accounting breach; further captures refused\n', valid.replace('coverage=complete','coverage=unknown',1), valid.replace('coverage=complete','coverage=incomplete',1)):
    try:
        r.protected_evidence(invalid, rows, True)
    except RuntimeError:
        pass
    else:
        raise AssertionError('invalid memory/coverage evidence accepted')

MOCK = r'''import hashlib,json,os,queue,sys,threading,time
from pathlib import Path
mode=sys.argv[1]
if len(sys.argv)>2:Path(sys.argv[2]).write_text(str(os.getpid()))
q=queue.Queue();stop=threading.Event()
def reader():
 for line in sys.stdin:
  if line.strip()=='STOP':stop.set()
  else:q.put(line.strip())
 q.put('QUIT')
threading.Thread(target=reader,daemon=True).start()
print('INFO context=262144 kv=int8',flush=True)
print('READY 262144 stop',flush=True)
i=0
while True:
 line=q.get()
 if line=='QUIT':break
 if mode=='timeout':time.sleep(60)
 if mode=='error':print('ERR mock failure',flush=True);continue
 if mode=='eof':break
 stop.clear();i+=1
 fields=line.split();nmax=int(fields[1]);ids=list(map(int,fields[-1].split(',')));n=len(ids)
 value=int(hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()[:8],16)%190000
 count=0;finish='length'
 for j in range(nmax):
  print('T '+str((value+j)%200000),flush=True);count+=1
  time.sleep(.001)
  if stop.is_set():finish='cancel';break
 reused=0
 if i==8:reused=100786 if mode=='candidate' else 10674
 if i==10:reused=131074 if mode=='candidate' else 130897
 print(f'DONE {count} {n} 1.0 1.0 {finish} 0 0 {reused} 0 0 0 0 0.0 {n-reused} 0',flush=True)
 if mode=='candidate':
  if i==9:print('[protected-cache] req=9 event=captured len=131074 target=131072 source=decode bytes=512 owned=1024 total=1024 reserved=0 high_water=2048 limit=17179869184 coverage=complete ms=0.5',file=sys.stderr,flush=True)
  print(f'[protected-cache] req={i} event=request_complete owned=960 total=1024 reserved=64 high_water=2048 limit=17179869184 coverage=complete',file=sys.stderr,flush=True)
'''
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    mock = tmp / 'mock.py'
    mock.write_text(MOCK)
    for mode in ('baseline','candidate','timeout','error','eof'):
        command = tmp / (mode + '-command.json')
        pid = tmp / (mode + '.pid')
        command.write_text(json.dumps([sys.executable,str(mock),mode,str(pid)]))
        argv = [sys.executable,'-B',str(HERE/'replay.py'),'run','--command',str(command),'--seed',str(HERE/'prompt-65536.ids.json'),'--out',str(tmp/mode),'--tag',mode,'--binary-sha256','CPU_MOCK_ONLY','--request-timeout','0.2' if mode=='timeout' else '10','--arm-timeout','30']
        if mode=='candidate':argv.append('--require-protected')
        p = subprocess.run(argv,capture_output=True,text=True,timeout=40)
        if mode in ('baseline','candidate'):
            assert p.returncode == 0,p.stderr
            summary=json.loads((tmp/mode/'summary.json').read_text())
            assert summary['protocol_passed'] and summary['clean_native_exit']
        else:
            assert p.returncode != 0, mode
            assert (tmp/mode/'failure.json').exists()
        if pid.exists():
            try:os.kill(int(pid.read_text()),0)
            except ProcessLookupError:pass
            else:raise AssertionError('owned native process survived '+mode)
    result = subprocess.run([sys.executable,'-B',str(HERE/'replay.py'),'compare','--baseline',str(tmp/'baseline'),'--candidate',str(tmp/'candidate')],capture_output=True,text=True,timeout=10)
    assert result.returncode == 0,result.stderr
    data=json.loads(result.stdout)
    assert data['all_inputs_identical'] and data['all_comparable_output_ids_equal'] and data['compaction_gain'] and data['decode_anchor_reuse']
    assert data['ordinary_short_turns']['baseline']['request_count']==6
    assert data['aggregate']['candidate']['capture_ms']==0.5
    assert 'candidate_wall_s' in data['rows'][0] and 'candidate_decode_ms' in data['rows'][0]
    assert data['rows'][0]['candidate_first_token_ms']>0
    assert data['ordinary_short_turns']['candidate']['first_token_ms_mean']>0
    changed=json.loads((tmp/'candidate'/'results.json').read_text());changed[0]['output_ids'][0]+=1
    (tmp/'candidate'/'results.json').write_text(json.dumps(changed))
    p=subprocess.run([sys.executable,'-B',str(HERE/'replay.py'),'compare','--baseline',str(tmp/'baseline'),'--candidate',str(tmp/'candidate')],capture_output=True,text=True,timeout=10)
    assert p.returncode != 0,'parity regression accepted'
spec = importlib.util.spec_from_file_location('launcher', HERE / 'run_gpu_replay.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
env=json.loads((HERE/'production-environment.json').read_text())
args=['--max-context','262144','--prompt-cache','6','--prefill','4096','--spec','6','--vision','--eos-ids','1,2']
cmd0=launcher.command('/srv/strata/logs/base/strata',args,env,'owned-base','TEST',False)
cmd1=launcher.command('/srv/strata/logs/new/strata',args,env,'owned-candidate','TEST',True)
assert cmd0.count('--prompt-cache-spread')==1 and cmd1.count('--prompt-cache-spread')==1
assert '--prompt-cache-protected' not in cmd0 and cmd1.count('--prompt-cache-protected')==1
assert cmd1[cmd1.index('--network')+1]=='none' and '--pull=never' in cmd1
assert cmd1[cmd1.index('--eos-ids')+1]=='2147483647' and '1,2' not in cmd1
assert all(':' not in value or not value.endswith(':rw') for value in cmd1)
launcher.sh=lambda argv,timeout=30: 'containerid' if argv[:3]==['docker','ps','-aq'] else 'FOREIGN'
try:launcher.cleanup('foreign','TEST')
except RuntimeError as error:assert 'foreign' in str(error)
else:raise AssertionError('foreign cleanup was allowed')
print('PASS: exact-LCP dynamic fixtures; 13-request native protocol per arm; bounded cancel/recovery; exact full/comparable-prefix parity; single-count 16GiB memory validation; timeout/ERR/EOF cleanup and negative gates. CPU mock only; no GPU execution.')
