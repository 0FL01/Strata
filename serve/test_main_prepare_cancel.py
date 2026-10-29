import copy
import pathlib,unittest,json
import io,threading,contextlib,inspect
from unittest import mock
from types import SimpleNamespace
from serve import server
from serve.server import ByteTokenizer,MockEngine,Service
from serve.frontend import ChatTemplate
class PrepareCancel(unittest.TestCase):
 def svc(self):
  tok=ByteTokenizer();return Service(MockEngine(tok,'ok',max_context=4096),tok,ChatTemplate(pathlib.Path(__file__).with_name('chat_template.jinja')))
 def test_precancel_no_prompt_encode(self):
  svc=self.svc();cancel=threading.Event();cancel.set();svc.encode_prompt=mock.Mock(side_effect=AssertionError('encoding started'))
  self.assertIn('cancel',inspect.signature(svc.prepare).parameters)
  with self.assertRaises(server.ClientGone):svc.prepare([],None,{},10,cancel=cancel)
  svc.encode_prompt.assert_not_called()
 def test_turn_cancel_on_success_releases_only_owner(self):
  svc=self.svc();cancel=threading.Event();lock=mock.Mock()
  lock.acquire.side_effect=lambda **kw:(cancel.set() or True);svc.fifo=lock
  with self.assertRaises(server.ClientGone):
   with svc._turn(cancel):self.fail('entered cancelled turn')
  lock.release.assert_called_once()
 def test_turn_precancel_never_acquires(self):
  svc=self.svc();cancel=threading.Event();cancel.set();svc.fifo=mock.Mock()
  with self.assertRaises(server.ClientGone):
   with svc._turn(cancel):self.fail('entered')
  svc.fifo.acquire.assert_not_called();svc.fifo.release.assert_not_called()
 def test_turn_acquire_error_never_releases(self):
  svc=self.svc();svc.fifo=mock.Mock();svc.fifo.acquire.side_effect=RuntimeError('lock')
  with self.assertRaisesRegex(RuntimeError,'lock'):
   with svc._turn(threading.Event()):pass
  svc.fifo.release.assert_not_called()
 def test_cancel_during_first_or_last_image_skips_combine(self):
  for count in (1,2):
   with self.subTest(count=count):
    svc=self.svc();cancel=threading.Event();seen=[]
    def encode(src):seen.append(src);cancel.set();return pathlib.Path('/not-created.sve'),1
    svc.vision=SimpleNamespace(encode=encode,dir='/tmp')
    messages=[{'role':'user','content':[{'type':'image','source':f'fake{i}'} for i in range(count)]}]
    with mock.patch.object(server,'combined_embeddings_path',side_effect=AssertionError('combine started')):
     with self.assertRaises(server.ClientGone):svc.prepare(messages,None,{'enable_thinking':False},10,cancel=cancel)
    self.assertEqual(seen,['fake0']);self.assertIsNone(svc.embeddings.path)
 def test_actual_handlers_watch_before_prepare(self):
  for path in ('/v1/chat/completions','/v1/messages','/v1/responses'):
   for stream in (False,True):
    with self.subTest(path=path,stream=stream):
     svc=self.svc();svc.encode_prompt=mock.Mock(side_effect=AssertionError('prompt work after cancel'))
     body={'model':'m','stream':stream,'max_tokens':10,'messages':[{'role':'user','content':'hi'}]}
     if path=='/v1/responses':body={'model':'m','stream':stream,'max_output_tokens':10,'input':'hi'}
     data=json.dumps(body).encode();h=object.__new__(server.make_handler(svc));h.path=path
     h.headers={'Content-Length':str(len(data)),'Content-Type':'application/json'};h.rfile=io.BytesIO(data);h.wfile=io.BytesIO();h.record=None
     h._authorized=lambda:True;h._foreign_page=lambda:False;h._watch_client=lambda cancel:cancel.set()
     notes=[];responses=[];h._note=lambda *a,**k:notes.append(k);h._json=lambda *a:responses.append(a)
     with contextlib.redirect_stdout(io.StringIO()):h.do_POST()
     svc.encode_prompt.assert_not_called();self.assertEqual(responses,[])
     self.assertTrue(any(n.get('outcome')=='disconnected' for n in notes))

class MainPrepareBoundaries(unittest.TestCase):
 svc = PrepareCancel.svc
 def test_real_encode_all_keeps_prior_files_and_checks_between_images(self):
  for cancel_after in (None,1,2):
   with self.subTest(cancel_after=cancel_after):
    cancel=threading.Event();seen=[]
    def encode(src,keep=()):
     seen.append((src,list(keep)))
     if len(seen)==cancel_after:cancel.set()
     return pathlib.Path('/tmp/'+src+'.sve'),1
    vision=SimpleNamespace(encode=encode)
    if cancel_after==1:
     with self.assertRaises(server.ClientGone):server.Vision.encode_all(vision,['a','b'],cancel)
    else:
     result=server.Vision.encode_all(vision,['a','b'],cancel)
     self.assertEqual(len(result),2)
     self.assertEqual(seen[1][1],[pathlib.Path('/tmp/a.sve')])
    self.assertEqual(len(seen),1 if cancel_after==1 else 2)
 def test_cancel_after_encode_all_last_image_skips_file_access(self):
  svc=self.svc();cancel=threading.Event();calls=[]
  def encode_all(images,event):
   self.assertIs(event,cancel);calls.append(list(images));cancel.set()
   return [(pathlib.Path('/never-created.sve'),1)]
  svc.vision=SimpleNamespace(encode_all=encode_all,dir='/tmp')
  messages=[{'role':'user','content':[{'type':'image','source':'fake'}]}]
  with mock.patch.object(server,'combined_embeddings_path',side_effect=AssertionError('combine')):
   with self.assertRaises(server.ClientGone):svc.prepare(messages,None,{'enable_thinking':False},10,cancel=cancel)
  self.assertEqual(calls,[['fake']]);self.assertIsNone(svc.embeddings.path)
  self.assertGreater(svc.last_image_at,0)
 def test_cancel_after_tool_image_preparation_skips_prompt(self):
  svc=self.svc();cancel=threading.Event()
  svc._note_unreadable_tool_images=lambda *args:(cancel.set() or {})
  svc.encode_prompt=mock.Mock(side_effect=AssertionError('prompt'))
  with self.assertRaises(server.ClientGone):svc.prepare([],None,{},10,cancel=cancel)
  svc.encode_prompt.assert_not_called()
 def test_normal_prepare_unchanged(self):
  svc=self.svc();messages=[{'role':'user','content':'hello'}]
  a=svc.prepare(copy.deepcopy(messages),None,{'enable_thinking':False},10)
  b=svc.prepare(copy.deepcopy(messages),None,{'enable_thinking':False},10,cancel=threading.Event())
  self.assertEqual(a,b)
