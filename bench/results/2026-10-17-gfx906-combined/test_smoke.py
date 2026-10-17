import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import protocol
from test_runner import PROMPT

HERE=Path(__file__).parent
FAKE='''#!/usr/bin/env python3
import os,sys
if sys.argv[1]=='inspect':
 print('error: no such object: '+sys.argv[-1],file=sys.stderr);sys.exit(1)
assert sys.argv[1]=='run'
on='TEST_NEW=1' in sys.argv
print('INFO context=262144 kv=int8 kv_resident=32768 pool_workers=15 spec=6 mtp_max=4 lookup=0 prefill_cap=4096 engine='+('different' if os.environ.get('FAKE_ENGINE') and on else '0.1.45'),flush=True)
print('verified device split',file=sys.stderr,flush=True)
print('READY 262144 stop',flush=True)
line=sys.stdin.readline()
assert line.startswith('GEN 256 temperature=0 top_p=1 top_k=1 seed=12345 ')
assert len(line.split()[-1].split(','))==4096
print('RESUME 0')
print('PP 4093 4096 100 40')
print('PP 4095 4096 100 40')
print('REUSED 0')
for i in range(256):print('T '+('2' if os.environ.get('FAKE_MISMATCH') and on else '1'))
print('DONE 256 4096 100 100 length 1 2 0 0 0 4 0 0.0 4096 0 chunk=4096 experts_streamed=16000',flush=True)
assert sys.stdin.readline()=='QUIT\\n'
'''

class Smoke(unittest.TestCase):
 def case(self,mutation=None):
  with tempfile.TemporaryDirectory(prefix='short-smoke-') as d:
   d=Path(d);fake=d/'docker';fake.write_text(FAKE);fake.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text());cfg.update(lock_path=str(d/'lock'),prompt=str(PROMPT),executables={'A':'/baseline','B':'/candidate'},docker_options=[],args=[],required_stderr_fragments=['verified device split'],environment={'STRATA_ROUTE_TAIL_SKIP':'0'},treatment_environment={'A':{},'B':{'TEST_NEW':'1'}})
   (d/'cfg').write_text(json.dumps(cfg));env=dict(os.environ,PATH=str(d)+':'+os.environ['PATH'])
   if mutation:env[mutation]='1'
   p=subprocess.run([sys.executable,str(HERE/'run_smoke.py'),str(d/'cfg'),str(d/'out')],env=env,capture_output=True,text=True,timeout=15)
   state=json.loads((d/'out/status.json').read_text())
   if mutation:
    self.assertNotEqual(p.returncode,0);self.assertEqual(state['state'],'failed');self.assertEqual(len(state['rows']),2)
    self.assertEqual(json.loads((d/'out/smoke-B.receipt.json').read_text())['state'],'rejected')
   else:
    self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(state['state'],'complete');self.assertEqual([r['arm'] for r in state['rows']],['A','C','B'])
    self.assertFalse(state['performance_qualified']);self.assertFalse(state['quality_claim'])
    self.assertTrue(all(len(r['output_ids'])==256 for r in state['rows']))
    self.assertFalse((d/'out/summary.json').exists())
    self.assertNotIn('prompt_ms',state['rows'][0]);self.assertIn('engine',state['rows'][0]['info'])
    c=json.loads((d/'out/smoke-C.receipt.json').read_text())['command'];self.assertIn('/candidate',c);self.assertNotIn('TEST_NEW=1',c)
    b=json.loads((d/'out/smoke-B.receipt.json').read_text())['command'];self.assertIn('TEST_NEW=1',b)
    raw=(d/'out/smoke-A.stdout').read_text()
    with self.assertRaisesRegex(ValueError,'work mismatch'):protocol.parse(raw)
    row=protocol.parse(raw,prompt_count=4096,output_count=256,ignore_info_fields=('vram_free_mib',))
    rows=[dict(row,pair=i,arm=a) for i,o in enumerate(protocol.ORDER,1) for a in o]
    with self.assertRaisesRegex(ValueError,'fixed 65536/1024'):protocol.summary(rows)
 def test_acb_success_and_fixed_perf_gate(self):self.case()
 def test_output_mismatch(self):self.case('FAKE_MISMATCH')
 def test_engine_mismatch(self):self.case('FAKE_ENGINE')
if __name__=='__main__':unittest.main()
