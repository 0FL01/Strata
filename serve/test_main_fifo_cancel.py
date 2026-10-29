import pathlib,unittest,json
import io,threading,contextlib
from unittest import mock
from serve import server
from serve.server import ByteTokenizer,MockEngine,Service
from serve.frontend import ChatTemplate
class FifoCancel(unittest.TestCase):
 def setup_case(self,kind):
  tok=ByteTokenizer();cancel=threading.Event();now=[0.0];calls=[]
  class Engine(MockEngine):
   def generate(self,*a,**k):calls.append('generate');yield from super().generate(*a,**k)
  eng=Engine(tok,'ok',max_context=4096);svc=Service(eng,tok,ChatTemplate(pathlib.Path(__file__).with_name('chat_template.jinja')))
  svc.ensure_loaded=lambda:calls.append('load')
  class Lock:
   acquired=0;released=0;waits=[]
   def acquire(self,timeout=None,**kw):
    self.waits.append(timeout);now[0]+=timeout or 0
    if kind=='queued':return False
    if kind=='wait_cancel':cancel.set();return False
    if kind=='error':raise RuntimeError('injected acquire error')
    if kind=='during':cancel.set()
    self.acquired+=1;return True
   def release(self):self.released+=1
   def __enter__(self):self.acquire();return self
   def __exit__(self,*a):self.release()
  lock=Lock();svc.fifo=lock
  if kind=='before':cancel.set()
  return svc,tok,cancel,now,calls,lock
 def test_precancel_does_not_take_or_start(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('before')
  rows=list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(calls,[]);self.assertEqual(lock.acquired,0);self.assertEqual(lock.released,0)
  self.assertEqual(svc.status['queued'],0);self.assertEqual(rows[-1][1]['finish'],'cancel')
 def test_cancel_on_successful_acquire(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('during')
  rows=list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(calls,[]);self.assertEqual(lock.acquired,1);self.assertEqual(lock.released,1)
  self.assertEqual(svc.status['queued'],0);self.assertEqual(rows[-1][1]['finish'],'cancel')
 def test_close_queued_ping_never_releases_other_owner(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('queued')
  with mock.patch.object(server.time,'monotonic',lambda:now[0]):
   gen=svc.run(tok.encode('hi'),False,None,10,{},cancel)
   self.assertEqual(next(gen),('ping',None));self.assertEqual(now[0],10.0);gen.close()
  self.assertEqual(calls,[]);self.assertEqual(lock.acquired,0);self.assertEqual(lock.released,0)
  self.assertEqual(svc.status['queued'],0);self.assertTrue(all(t<=.25 for t in lock.waits))
 def test_normal_work_releases_once(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('success')
  with contextlib.redirect_stdout(io.StringIO()):rows=list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(calls,['load','generate']);self.assertEqual(lock.released,1);self.assertEqual(svc.status['queued'],0)
 def test_cancel_while_waiting(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('wait_cancel')
  rows=list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(calls,[]);self.assertEqual(lock.released,0);self.assertEqual(svc.status['queued'],0)
  self.assertEqual(lock.waits,[.25]);self.assertEqual(rows[-1][1]['finish'],'cancel')
 def test_acquire_exception_does_not_release_foreign_lock(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('error')
  with self.assertRaisesRegex(RuntimeError,'injected'):list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(calls,[]);self.assertEqual(lock.released,0);self.assertEqual(svc.status['queued'],0)

class FifoFailure(unittest.TestCase):
 setup_case = FifoCancel.setup_case
 def test_loaded_failure_releases_owned_turn_once(self):
  svc,tok,cancel,now,calls,lock=self.setup_case('success')
  def fail():raise RuntimeError('injected load failure')
  svc.ensure_loaded=fail
  with self.assertRaisesRegex(RuntimeError,'injected load failure'):
   list(svc.run(tok.encode('hi'),False,None,10,{},cancel))
  self.assertEqual(lock.acquired,1);self.assertEqual(lock.released,1)
  self.assertEqual(svc.status['queued'],0)
