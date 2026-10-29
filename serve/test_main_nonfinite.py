import pathlib,unittest,json
import contextlib,io,threading
from types import SimpleNamespace
from serve.frontend import ChatTemplate
from serve import server
from serve.server import ByteTokenizer,EngineDied,MockEngine,Service,StrataEngine
class MissingNonFinite(ValueError):pass
EngineNonFinite=getattr(server,'EngineNonFinite',MissingNonFinite)
ROOT=pathlib.Path(__file__).resolve().parents[1];CTX=4096
class NonFiniteEngine(MockEngine):
    """#879: each pass ends on the engine's `DONE ... nonfinite` after plan[i] tokens (None, or no plan left: the
    script runs whole), as StrataEngine.generate raises it.  A pass that ends on it had reused all but the last
    prompt token; the next one reads from token 0, as the engine does."""

    def __init__(self, *a, plan=(), **kw):
        super().__init__(*a, **kw)
        self.plan, self.calls = (list(plan), [])
        self.last, self.flushed = (None, False)

    def generate(self, ids, max_new, sampling, cancel, embeddings=None):
        self.calls.append(list(ids))
        cut = self.plan.pop(0) if self.plan else None
        self.last = {'prompt_tokens': len(ids), 'reused': 0 if self.flushed else len(ids) - 1, 'finish': 'nonfinite' if cut is not None else 'stop'}
        self.flushed = False
        for i, t in enumerate(super().generate(ids, max_new, sampling, cancel, embeddings)):
            if cut is not None and i >= cut:
                break
            yield t
        if cut is not None:
            self.flushed = True
            raise EngineNonFinite("the engine's logits became non-finite (#879)")

class NonFiniteLogits(unittest.TestCase):
    """#879: non-finite logits before the first token -> the same request once more; after tokens went out -> the
    reply ends as "length"; again on the retry -> an error, no loop."""

    def run_reply(self, plan):
        tok = ByteTokenizer()
        eng = NonFiniteEngine(tok, 'hello', max_context=CTX, plan=plan)
        svc = Service(eng, tok, ChatTemplate(ROOT / 'serve/chat_template.jinja'))
        ids = tok.encode('hi')
        events, done, error = ([], None, None)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            try:
                for kind, x in svc.run(ids, False, None, 100, {}, threading.Event()):
                    if kind == 'done':
                        done = x
                    elif kind == 'event':
                        events.append(x)
            except EngineNonFinite as e:
                error = e
        text = ''.join((ev.text or '' for ev in events if ev.kind == 'content'))
        return (eng, svc, ids, done, error, text, out.getvalue())

    def test_nothing_emitted_is_retried_once(self):
        eng, svc, ids, done, error, text, log = self.run_reply([0])
        self.assertIsNone(error)
        self.assertEqual(eng.calls, [ids, ids])
        self.assertEqual(done['finish'], 'stop')
        self.assertEqual(text, 'hello')
        self.assertIn('non-finite before the first token', log)
        self.assertEqual(svc.metrics()['requests'][0]['finish'], 'stop')
        self.assertEqual(svc.metrics()['requests'][0]['reused'], 0)

    def test_mid_reply_ends_without_retry(self):
        eng, svc, ids, done, error, text, log = self.run_reply([3])
        self.assertIsNone(error)
        self.assertEqual(len(eng.calls), 1)
        self.assertEqual((done['finish'], done['completion_tokens']), ('length', 3))
        self.assertEqual(text, 'hel')
        self.assertIn('non-finite after 3 tokens', log)

    def test_twice_is_an_error(self):
        eng, svc, ids, done, error, text, log = self.run_reply([0, 0, 0])
        self.assertIsNotNone(error)
        self.assertIn('twice in a row', str(error))
        self.assertEqual(eng.calls, [ids, ids])
        self.assertEqual(eng.plan, [0])
        self.assertIsNone(done)
        self.assertEqual(svc.metrics()['requests'][0]['finish'], 'error')

    def test_engine_done_line_raises(self):
        """StrataEngine.generate: `DONE ... nonfinite` raises EngineNonFinite after the tokens before it."""
        import queue as queue_
        eng = object.__new__(StrataEngine)
        eng.lines = queue_.Queue()
        for line in ('T 5', 'T 6', 'DONE 2 3 1.0 2.0 nonfinite 0 0 0'):
            eng.lines.put(line)
        eng.proc = SimpleNamespace(stdin=io.StringIO())
        eng.alive = lambda: True
        eng.silence_s, eng.can_stop, eng.last = (0, True, None)
        got = []
        with self.assertRaises(EngineNonFinite):
            for t in eng.generate([1, 2, 3], 10, {}, threading.Event()):
                got.append(t)
        self.assertEqual(got, [5, 6])
        self.assertEqual(eng.last['finish'], 'nonfinite')
        self.assertNotIn('STOP', eng.proc.stdin.getvalue())

class NonFiniteLifecycle(unittest.TestCase):
 def exercise(self,mode,thinking=False):
  tok=ByteTokenizer();cancel=threading.Event()
  class Engine(NonFiniteEngine):
   def generate(self,ids,max_new,sampling,cancel,embeddings=None):
    if not self.calls:
     if mode=='cancel_first':cancel.set()
     yield from super().generate(ids,max_new,sampling,cancel,embeddings)
    else:
     self.calls.append(list(ids))
     if mode=='death':raise EngineDied('injected retry death')
     cancel.set()
     return
     yield
  eng=Engine(tok,'hello',max_context=CTX,plan=[0])
  svc=Service(eng,tok,ChatTemplate(ROOT/'serve/chat_template.jinja'))
  done=None;err=None
  with contextlib.redirect_stdout(io.StringIO()):
   try:
    for kind,x in svc.run(tok.encode('hi'),thinking,None,100,{},cancel):
     if kind=='done':done=x
   except EngineDied as e:err=e
  return eng,svc,done,err
 def test_cancel_before_retry(self):
  eng,svc,done,err=self.exercise('cancel_first')
  self.assertEqual(len(eng.calls),1);self.assertEqual(done['finish'],'cancel')
 def test_retry_cancel_has_no_discarded_reuse(self):
  eng,svc,done,err=self.exercise('cancel')
  self.assertEqual(len(eng.calls),2);self.assertEqual(done['finish'],'cancel')
  row=svc.metrics()['requests'][0]
  self.assertIsNone(row['reused']);self.assertIsNone(row['prompt_ms'])
 def test_retry_death_has_no_discarded_reuse(self):
  eng,svc,done,err=self.exercise('death')
  self.assertIsNotNone(err);self.assertEqual(len(eng.calls),2)
  row=svc.metrics()['requests'][0]
  self.assertEqual(row['finish'],'error');self.assertIsNone(row['reused'])
 def test_midreply_preserves_work_metrics(self):
  eng,svc,ids,done,error,text,log=NonFiniteLogits().run_reply([3])
  row=svc.metrics()['requests'][0]
  self.assertEqual(row['output_tokens'],3);self.assertEqual(row['reused'],len(ids)-1)
 def test_second_failure_is_fresh_error_record(self):
  eng,svc,ids,done,error,text,log=NonFiniteLogits().run_reply([0,0])
  row=svc.metrics()['requests'][0]
  self.assertEqual(row['finish'],'error');self.assertEqual(row['reused'],0)
 def test_nonfinite_reasoning_never_1053(self):
  tok=ByteTokenizer();eng=NonFiniteEngine(tok,'thinking words',max_context=CTX,plan=[3])
  svc=Service(eng,tok,ChatTemplate(ROOT/'serve/chat_template.jinja'));svc.reasoning_close_retry=True
  with contextlib.redirect_stdout(io.StringIO()):
   rows=list(svc.run(tok.encode('hi'),True,None,100,{},threading.Event()))
  self.assertEqual(len(eng.calls),1)
  self.assertEqual([x for k,x in rows if k=='done'][0]['finish'],'length')
 def test_1053_preserved_with_and_without_initial_nf(self):
  for initial in (False,True):
   tok=ByteTokenizer()
   class Engine(MockEngine):
    def __init__(self):super().__init__(tok,'x',max_context=CTX);self.calls=[];self.last=None
    def generate(self,ids,max_new,sampling,cancel,embeddings=None):
     self.calls.append(list(ids))
     if initial and len(self.calls)==1:
      self.last={'finish':'nonfinite','reused':len(ids)-1}
      raise EngineNonFinite('first')
     closed=tok.decode(ids).endswith('</think>\n\n')
     text='answer' if closed else 'I think.'
     yield from (tok.encode(text)+tok.encode('<|im_end|>',parse_special=True))[:max_new]
   eng=Engine();svc=Service(eng,tok,ChatTemplate(ROOT/'serve/chat_template.jinja'));svc.reasoning_close_retry=True
   with contextlib.redirect_stdout(io.StringIO()):
    rows=list(svc.run(tok.encode('hi'),True,None,100,{},threading.Event()))
   self.assertEqual(len(eng.calls),3 if initial else 2)
   self.assertEqual([x for k,x in rows if k=='done'][0]['finish'],'stop')

class NonFiniteWire(unittest.TestCase):
 def test_actual_handlers_no_network(self):
  for path in ('/v1/chat/completions','/v1/messages','/v1/responses'):
   for stream in (False,True):
    for plan in ([0],[0,0],[3]):
     with self.subTest(path=path,stream=stream,plan=plan):
      tok=ByteTokenizer();eng=NonFiniteEngine(tok,'hello',max_context=CTX,plan=plan)
      svc=Service(eng,tok,ChatTemplate(ROOT/'serve/chat_template.jinja'))
      body={'model':'m','stream':stream,'max_tokens':100,'messages':[{'role':'user','content':'hi'}],
            'enable_thinking':False,'chat_template_kwargs':{'enable_thinking':False}}
      if path=='/v1/responses':
       body={'model':'m','stream':stream,'max_output_tokens':100,'input':'hi','reasoning':{'effort':'none'}}
      data=json.dumps(body).encode()
      h=object.__new__(server.make_handler(svc));h.path=path
      h.headers={'Content-Length':str(len(data)),'Content-Type':'application/json'}
      h.rfile=io.BytesIO(data);h.wfile=io.BytesIO();h.record=None
      h._authorized=lambda:True;h._foreign_page=lambda:False
      h._watch_client=lambda cancel:None;h._note=lambda *a,**k:None
      responses=[]
      h._json=lambda status,body:responses.append((status,body))
      h._sse=lambda:responses.append((200,{}))
      with contextlib.redirect_stdout(io.StringIO()):h.do_POST()
      self.assertEqual(responses[0][0],503 if plan==[0,0] and not stream else 200)
      payload=json.dumps(responses)+h.wfile.getvalue().decode()
      if plan==[0,0]:self.assertIn('twice in a row',payload)
      self.assertEqual(len(eng.calls),2 if plan in ([0],[0,0]) else 1)
