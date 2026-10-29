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
from serve import test_vision_prepare_lifetime
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [test_vision_prepare_lifetime.VisionCacheLifetime,test_vision_prepare_lifetime.PrepareOwnership,test_vision_prepare_lifetime.CurrentVisionCachePolicy])
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
