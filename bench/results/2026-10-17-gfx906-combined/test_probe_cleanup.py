"""Exercise the real probe main with a SIGTERM-resistant fake Docker client."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import probe_startup as probe

HERE=Path(__file__).parent
FAKE='''#!/usr/bin/env python3
import os,signal,sys,time
if sys.argv[1]=='inspect':
 print('Error: No such object: '+sys.argv[-1],file=sys.stderr);sys.exit(1)
assert sys.argv[1]=='run'
signal.signal(signal.SIGTERM,signal.SIG_IGN)
print('INFO context=262144 kv=int8',flush=True)
print('READY 262144 stop',flush=True)
assert sys.stdin.readline()=='QUIT\\n'
while True:time.sleep(.01)
'''

class ProbeCleanup(unittest.TestCase):
 def test_cleanup_exception_still_kills_and_reaps_resistant_client(self):
  with tempfile.TemporaryDirectory(prefix='probe-cleanup-') as d:
   d=Path(d);docker=d/'docker';docker.write_text(FAKE);docker.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text())
   cfg.update(lock_path=str(d/'lock'),docker_options=[],args=[],executables={'A':'/baseline'},quit_timeout_s=.05,interrupt_grace_s=.05,client_reap_timeout_s=.2)
   config=d/'config';config.write_text(json.dumps(cfg));out=d/'out'
   with patch.dict(os.environ,{'PATH':str(d)+':'+os.environ['PATH']}),patch('sys.argv',['probe_startup.py',str(config),str(out)]),patch.object(probe,'cleanup',side_effect=RuntimeError('injected inspect failure')):
    with self.assertRaisesRegex(RuntimeError,'injected inspect failure'):probe.main()
   receipt=json.loads((out/'receipt.json').read_text())
   self.assertEqual(receipt['state'],'cleanup_failed')
   self.assertIn('injected inspect failure',receipt['cleanup_error'])
   self.assertTrue(receipt['client_reaped']);self.assertTrue(receipt['reader_exited'])
   self.assertEqual(receipt['client_exit_code'],-9)
   with self.assertRaises(ProcessLookupError):os.kill(receipt['docker_client_pid'],0)
if __name__=='__main__':unittest.main()

class ClosedProbeGates(unittest.TestCase):
 def run_fake(self,stdout,stderr='',exit_code=0):
  with tempfile.TemporaryDirectory(prefix='probe-replay-') as d:
   d=Path(d);docker=d/'docker'
   script='#!/usr/bin/env python3\nimport sys\nif sys.argv[1]=="inspect":\n print("Error: No such object: "+sys.argv[-1],file=sys.stderr);sys.exit(1)\n'
   script+=f'print({stdout!r},flush=True)\nprint({stderr!r},file=sys.stderr,flush=True)\nsys.stdin.readline()\nsys.exit({exit_code})\n'
   docker.write_text(script);docker.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text());cfg.update(lock_path=str(d/'lock'),docker_options=[],args=[],executables={'A':'/baseline'})
   config=d/'config';config.write_text(json.dumps(cfg));out=d/'out'
   error=None
   with patch.dict(os.environ,{'PATH':str(d)+':'+os.environ['PATH']}),patch('sys.argv',['probe_startup.py',str(config),str(out)]),patch('builtins.print'):
    try:probe.main()
    except (ValueError,RuntimeError) as exc:error=exc
   receipt=json.loads((out/'receipt.json').read_text())
   self.assertTrue(receipt['client_reaped']);self.assertTrue(receipt['reader_exited'])
   return error,receipt
 def test_clean(self):
  error,r=self.run_fake('INFO context=262144 kv=int8\nREADY 262144 stop');self.assertIsNone(error);self.assertEqual(r['state'],'complete')
 def test_post_ready_error(self):
  error,r=self.run_fake('INFO context=262144\nREADY 262144 stop\nERR shutdown failure');self.assertIsNotNone(error);self.assertEqual(r['state'],'failed')
 def test_stderr_fatal(self):
  error,r=self.run_fake('INFO context=262144\nREADY 262144 stop','FATAL startup failure');self.assertIsNotNone(error);self.assertEqual(r['state'],'failed')
 def test_wrong_ready(self):
  error,r=self.run_fake('INFO context=100\nREADY 100 stop');self.assertIsNotNone(error)
 def test_info_after_ready(self):
  error,r=self.run_fake('READY 262144 stop\nINFO context=262144');self.assertIsNotNone(error)
 def test_duplicate_info(self):
  error,r=self.run_fake('INFO context=262144\nINFO context=262144\nREADY 262144 stop');self.assertIsNotNone(error)
