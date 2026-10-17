"""Real probe-main regression for the host's lowercase Docker missing-name error."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
import probe_startup as probe
import run_pairs as runner

HERE=Path(__file__).parent
NAME='strata-startup-2ea2562b4a72'

class InspectAbsence(unittest.TestCase):
 def main_case(self,error,success):
  with tempfile.TemporaryDirectory(prefix='probe-inspect-') as d:
   d=Path(d);marker=d/'run-called';docker=d/'docker'
   docker.write_text('#!/usr/bin/env python3\nimport sys,pathlib\n'+
    'if sys.argv[1]=="inspect":\n'+f' sys.stderr.write({error!r});sys.exit(1)\n'+
    'assert sys.argv[1]=="run"\n'+f'pathlib.Path({str(marker)!r}).write_text("started")\n'+
    'print("INFO context=262144 kv=int8",flush=True)\nprint("READY 262144 stop",flush=True)\nassert sys.stdin.readline()=="QUIT\\n"\n')
   docker.chmod(0o755)
   cfg=json.loads((HERE/'CONFIG.test.json').read_text());cfg.update(lock_path=str(d/'lock'),docker_options=[],args=[],executables={'A':'/baseline'})
   config=d/'config';config.write_text(json.dumps(cfg));out=d/'out'
   with patch.dict(os.environ,{'PATH':str(d)+':'+os.environ['PATH']}),patch('sys.argv',['probe_startup.py',str(config),str(out)]),patch.object(probe.uuid,'uuid4',return_value=types.SimpleNamespace(hex='2ea2562b4a72'+'0'*20)),patch('builtins.print'):
    if success:probe.main()
    else:
     with self.assertRaisesRegex(ValueError,'cannot inspect container'):probe.main()
   receipt=json.loads((out/'receipt.json').read_text())
   self.assertEqual(receipt['container'],NAME)
   self.assertEqual(marker.exists(),success)
   self.assertEqual(receipt['state'],'complete' if success else 'cleanup_failed')
   self.assertEqual(receipt['generation_requests'],0)
 def test_exact_host_lowercase(self):self.main_case('error: no such object: strata-startup-2ea2562b4a72\n',True)
 def test_uppercase(self):self.main_case('Error: No such object: '+NAME+'\n',True)
 def test_daemon_container_variant(self):self.main_case('Error response from daemon: No such container: '+NAME+'\n',True)
 def test_permission_failure(self):self.main_case('permission denied while trying to connect to the Docker daemon socket\n',False)
 def test_other_container_name(self):self.main_case('error: no such object: unrelated-name\n',False)
 def test_extra_error_line(self):self.main_case('error: no such object: '+NAME+'\npermission denied\n',False)
 def test_ambiguous_stdout(self):
  result=subprocess.CompletedProcess(['docker','inspect',NAME],1,'[{"unexpected":true}]','error: no such object: '+NAME+'\n')
  with patch.object(runner,'command',return_value=result):
   with self.assertRaisesRegex(ValueError,'cannot inspect container'):runner.owned(NAME,'owner')
if __name__=='__main__':unittest.main()
