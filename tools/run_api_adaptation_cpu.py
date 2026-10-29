import sys,os,pathlib,shutil,unittest,json
assert shutil.which('docker') is None
assert not pathlib.Path('/var/run/docker.sock').exists()
assert not pathlib.Path('/dev/kfd').exists()
assert not pathlib.Path('/dev/dri').exists()
assert not os.environ.get('DOCKER_HOST')
def audit(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork','os.forkpty','os.exec','os.kill','os.killpg'):
  raise RuntimeError('DENIED_EXTERNAL_EFFECT:'+event)
sys.addaudithook(audit)
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from serve import test_protocol_tool_results,test_chat_tool_results,test_frontend,test_tool_name_space,test_main_fifo_cancel,test_main_prepare_cancel,test_main_nonfinite,test_main_quiet_cancel,test_responses
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in [test_protocol_tool_results,test_chat_tool_results,test_frontend,test_tool_name_space,test_main_fifo_cancel,test_main_prepare_cancel,test_main_nonfinite,test_main_quiet_cancel])
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [test_responses.Parsing,test_responses.CodexCompaction])
if os.environ.get('API_TEST_SCOPE') == 'nonfinite':
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in [test_main_nonfinite,test_main_quiet_cancel])
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
