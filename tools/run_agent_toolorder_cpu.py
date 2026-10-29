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
sys.path.insert(0,'/src')
from serve import test_chat_tool_results,test_frontend,test_tool_name_space
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in [test_chat_tool_results,test_frontend,test_tool_name_space])
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
