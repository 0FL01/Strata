import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_runner import PROMPT

HERE=Path(__file__).parent
FAKE='''#!/usr/bin/env python3
import os,sys,json,hashlib
if sys.argv[1]=='inspect':
 print('error: no such object: '+sys.argv[-1],file=sys.stderr);sys.exit(1)
assert sys.argv[1]=='run'
on='TEST_NEW=1' in sys.argv
print('INFO context=262144 kv=int8 kv_resident=32768 pool_workers=15 spec=6 mtp_max=4 lookup=0 prefill_cap=4096 engine=0.1.45',flush=True)
print('verified device split',file=sys.stderr,flush=True)
print('READY 262144 stop',flush=True)
line=sys.stdin.readline()
assert line.startswith('GEN 1024 temperature=0 top_p=1 top_k=1 seed=12345 ')
ids=[int(x) for x in line.split()[-1].split(',')]
assert len(ids)==65536
assert hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()==os.environ['EXPECTED_IDS_SHA']
print('RESUME 0')
print('PP 4096 65536 100 40')
print('PP 65535 65536 100 40')
print('REUSED 0')
for i in range(1024):print('T '+('2' if os.environ.get('FAKE_MISMATCH') and on else '1'))
print('DONE 1024 65536 100 100 length 1 2 0 0 0 4 0 0.0 65536 0 chunk=4096 experts_streamed=16000',flush=True)
assert sys.stdin.readline()=='QUIT\\n'
'''

class Canary(unittest.TestCase):
 def case(self,mutation=None):
  with tempfile.TemporaryDirectory(prefix='full-canary-') as d:
   d=Path(d);fake=d/'docker';fake.write_text(FAKE);fake.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text());cfg.update(lock_path=str(d/'lock'),prompt=str(PROMPT),executables={'A':'/baseline','B':'/candidate'},docker_options=[],args=[],required_stderr_fragments=['verified device split'],environment={'STRATA_ROUTE_TAIL_SKIP':'0'},treatment_environment={'A':{},'B':{'TEST_NEW':'1'}})
   (d/'cfg').write_text(json.dumps(cfg));env=dict(os.environ,PATH=str(d)+':'+os.environ['PATH'],EXPECTED_IDS_SHA=hashlib.sha256(json.dumps(json.loads(PROMPT.read_text()),separators=(',',':')).encode()).hexdigest())
   if mutation:env[mutation]='1'
   cmd=[sys.executable,str(HERE/'run_canary.py'),str(d/'cfg'),str(d/'out')]
   p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=15)
   state=json.loads((d/'out/status.json').read_text())
   if mutation:
    self.assertNotEqual(p.returncode,0);self.assertEqual(state['state'],'failed');self.assertEqual(len(state['rows']),1)
    self.assertFalse(state['full_profile_canary_passed']);self.assertEqual(json.loads((d/'out/canary-B.receipt.json').read_text())['state'],'rejected')
   else:
    self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(state['state'],'complete');self.assertEqual([r['arm'] for r in state['rows']],['A','B'])
    self.assertTrue(state['full_profile_canary_passed']);self.assertFalse(state['performance_qualified']);self.assertFalse(state['quality_claim'])
    self.assertTrue(all(len(r['output_ids'])==1024 and r['counters']['read_n']=='65536' for r in state['rows']))
    self.assertFalse((d/'out/summary.json').exists());self.assertNotIn('prompt_ms',state['rows'][0])
    for arm in 'AB':
     receipt=json.loads((d/f'out/canary-{arm}.receipt.json').read_text());self.assertTrue(receipt['client_reaped']);self.assertTrue(receipt['reader_exited'])
    p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=5);self.assertNotEqual(p.returncode,0)
 def test_complete_exact_prompt_and_no_reuse(self):self.case()
 def test_parity_failure(self):self.case('FAKE_MISMATCH')
if __name__=='__main__':unittest.main()
