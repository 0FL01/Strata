"""Local fake-Docker integration only; never invokes a real Docker daemon."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).parent
PROMPT=HERE/'fixtures'/'prompt-65536.json'
FAKE='''#!/usr/bin/env python3
import sys,time,os,json
if sys.argv[1]=='inspect':
 print('Error: No such object: '+sys.argv[-1],file=sys.stderr);sys.exit(1)
if sys.argv[1]!='run':sys.exit(2)
arm='B' if '/candidate' in sys.argv else 'A'
print('INFO context=262144 kv=int8 kv_resident=32768 pool_workers=15 spec=6 mtp_max=4 lookup=0 prefill_cap=4096',flush=True)
print('verified device split',file=sys.stderr,flush=True)
print('READY 262144 stop',flush=True)
line=sys.stdin.readline()
assert line.startswith('GEN 1024 temperature=0 top_p=1 top_k=1 seed=12345 ')
assert len(line.split()[-1].split(','))==65536
print('RESUME 0')
print('PP 4096 65536 100 40')
print('PP 65535 65536 1000 65')
print('REUSED 0')
for i in range(1024):print('T '+('2' if os.environ.get('FAKE_MISMATCH') and arm=='B' else '1'))
print('DONE 1024 65536 '+('950' if arm=='B' else '1000')+' 100 length 0 0 0 0 0 4 0 0.0 65536 0 chunk=4096 experts_streamed=16000',flush=True)
assert sys.stdin.readline()=='QUIT\\n'
'''

class RunnerIntegration(unittest.TestCase):
 def run_case(self,mismatch=False):
  with tempfile.TemporaryDirectory(prefix='strata-fake-docker-') as d:
   d=Path(d);fake=d/'docker';fake.write_text(FAKE);fake.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text())
   cfg.update(lock_path=str(d/'lock'),prompt=str(PROMPT),executables={'A':'/baseline','B':'/candidate'},docker_options=[],args=[],required_stderr_fragments=['verified device split'])
   (d/'cfg.json').write_text(json.dumps(cfg))
   env=dict(os.environ,PATH=str(d)+':'+os.environ['PATH'])
   if mismatch:env['FAKE_MISMATCH']='1'
   cmd=[sys.executable,str(HERE/'run_pairs.py'),str(d/'cfg.json'),str(d/'results')]
   run=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=30)
   state=json.loads((d/'results/status.json').read_text())
   if mismatch:
    self.assertNotEqual(run.returncode,0);self.assertEqual(state['state'],'failed');self.assertFalse((d/'results/summary.json').exists())
    self.assertTrue((d/'results/01B.receipt.json').exists())
   else:
    self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(state['state'],'complete');self.assertEqual(len(state['rows']),12)
    self.assertTrue((d/'results/summary.json').exists())
    rerun=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=5)
    self.assertNotEqual(rerun.returncode,0)
 def test_complete_and_no_duplicate(self):self.run_case()
 def test_mismatch_stops(self):self.run_case(True)
if __name__=='__main__':unittest.main()
