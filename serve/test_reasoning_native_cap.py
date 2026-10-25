"""CPU-only actual Service/tokenizer tests. No native process, network, or model."""
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
import contextlib
import io
from serve import server
import strata_tokenizer as ST

SAFE_ARGS=["--pipeline-windows","2","--mtp-max-t","2","--suffix-draft","0","--no-coupled-draft"]

class CapEngine(server.MockEngine):
    """Native-cap simulation tied to the exact supplied raw prefix, not call index."""
    def __init__(self,tok,raw,answer,*,fault=None,cancel_after=None):
        super().__init__(tok,"",max_context=262144)
        self.raw=list(raw);self.answer=list(answer);self.wrap=tok.encode(server.REASONING_WRAP_UP,parse_special=True)
        self.spawn=("never-executed",SAFE_ARGS[:]);self.batch=0
        self.calls=[];self.receipts=[];self.base=None;self.last=None
        self.fault=fault;self.cancel_after=cancel_after
    def generate(self,ids,max_new,sampling,cancel,embeddings=None):
        assert embeddings is None and type(max_new)is int and max_new>0
        assert len(self.calls)<32,"unbounded continuation loop"
        if self.base is None:self.base=list(ids)
        assert list(ids[:len(self.base)])==self.base,"base prompt changed"
        suffix=list(ids[len(self.base):]);stream=self.raw;offset=len(suffix)
        found=[i for i in range(len(suffix)) if suffix[i:i+len(self.wrap)]==self.wrap]
        if found:
            assert len(found)==1
            i=found[0];assert suffix[:i]==self.raw[:i],"generated reasoning changed"
            suffix=suffix[i+len(self.wrap):];stream=self.answer;offset=len(suffix)
        assert suffix==stream[:offset],"continuation did not resume exact raw prefix"
        self.calls.append((list(ids),max_new,dict(sampling or {})))
        delivered=[];finish="cancel"
        try:
            if self.fault=="empty":
                finish="length";return
            for token in stream[offset:offset+max_new+(1 if self.fault=="overcap" else 0)]:
                if cancel.is_set():return
                if self.fault=="error":raise ValueError("scripted native failure")
                delivered.append(token)
                if self.cancel_after and sum(len(r["ids"]) for r in self.receipts)+len(delivered)>=self.cancel_after:
                    cancel.set()
                yield token
                if token in self.tok.encode(server.IM_END,parse_special=True):
                    finish="stop";return
            finish="length" if len(delivered)==max_new else "stop"
        finally:
            if delivered and delivered[-1] in self.tok.encode(server.IM_END,parse_special=True):finish="stop"
            if cancel.is_set():finish="cancel"
            self.last=dict(prompt_tokens=len(ids),generated=len(delivered),finish=finish,reused=0,
                           prompt_read=len(ids),prompt_ms=1.0,decode_ms=1.0)
            self.receipts.append({**self.last,"ids":delivered[:]})
            if self.fault=="wrong_done":self.last["generated"]=True
            if self.fault=="missing_done":self.last=None

def semantic(events):
    out={"reasoning":"","content":"","calls":[]}
    for kind,e in events:
        if kind!="event":continue
        if e.kind in ("reasoning","content"):out[e.kind]+=e.text or ""
        if e.kind=="tool_call":out["calls"].append((e.call.name,e.call.arguments))
    done=[v for k,v in events if k=="done"]
    assert len(done)==1
    out.update({k:done[0][k] for k in ("finish","completion_tokens","reasoning_tokens")})
    return out

class NativeCap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        location=os.environ.get("STRATA_TEST_TOKENIZER")
        if not location: raise unittest.SkipTest("set STRATA_TEST_TOKENIZER to the qualified tokenizer directory")
        root=Path(location)
        vocab=json.loads((root/"vocab.json").read_text());tokens=[None]*len(vocab)
        for token,index in vocab.items():tokens[index]=token
        cls.tok=ST.Tokenizer(tokens,(root/"merges.txt").read_text().split("\n"),json.loads((root/"token_type.json").read_text()))
        cls.wrap=cls.tok.encode(server.REASONING_WRAP_UP,parse_special=True)
        assert len(cls.wrap)==18,"this fixture requires the pinned current tokenizer"
        cls.eos=cls.tok.encode(server.IM_END,parse_special=True)
        cls.prompt=cls.tok.encode("<|im_start|>user\nTask<|im_end|>\n<|im_start|>assistant\n<think>\n",parse_special=True)
    def bytes(self,text):
        return [self.tok.ids[ST.BYTE_TO_UNICODE[b]] for b in text.encode("utf-8")]
    def run_case(self,flag,raw=None,answer=None,budget=8,maximum=256,fault=None,cancel_after=None,sampling=None,args=None):
        raw=self.bytes("abcdefghij"*10)+self.tok.encode("</think>\n\nNatural answer.")+self.eos if raw is None else raw
        answer=self.tok.encode("Final answer.")+self.eos if answer is None else answer
        engine=CapEngine(self.tok,raw,answer,fault=fault,cancel_after=cancel_after)
        if args is not None:engine.spawn=("never-executed",args)
        env=dict(os.environ);env.pop("STRATA_REASONING_NATIVE_CAP",None)
        if flag is not None:env["STRATA_REASONING_NATIVE_CAP"]=flag
        with patch.dict(os.environ,env,clear=True):
            svc=server.Service(engine,self.tok,None)
            svc.answer_room=False;svc.repeat_stop_tokens=0;svc.reasoning_loop_recovery=False
            events=list(svc.run(self.prompt,True,[{"name":"read","parameters":{"properties":{"path":{"type":"string"}}}}],maximum,
                               {"temperature":0,"reasoning_budget_tokens":budget,**(sampling or {})},threading.Event()))
        return engine,events
    def test_clean_wrap_and_default_off_requests(self):
        legacy,old=self.run_case(None)
        for flag in ("0","11",""):
            engine,events=self.run_case(flag)
            self.assertEqual(engine.calls,legacy.calls)
            self.assertEqual(semantic(events),semantic(old))
        engine,events=self.run_case("1")
        self.assertEqual(engine.calls[0][1],8)
        self.assertEqual(legacy.calls[0][1],256)
        self.assertEqual(len(engine.calls),2)
        self.assertEqual(engine.calls[1],legacy.calls[1])
        self.assertEqual(engine.calls[1][0],self.prompt+engine.raw[:8]+self.wrap)
        self.assertEqual(semantic(events),semantic(old))
        self.assertEqual(semantic(events)["completion_tokens"],8+18+len(engine.answer))
        self.assertEqual(engine.receipts[0]["finish"],"length")
    def test_tool_call_preserved(self):
        answer=self.tok.encode('<tool_call>\n<function=read>\n<parameter=path>\njobgraph.py\n</parameter>\n</function>\n</tool_call>',parse_special=True)+self.eos
        _,old=self.run_case(None,answer=answer)
        _,new=self.run_case("1",answer=answer)
        self.assertEqual(semantic(new),semantic(old))
        self.assertEqual(len(semantic(new)["calls"]),1)
    def test_early_close_continues_answer_without_wrap(self):
        raw=self.tok.encode("</think>\n\n"+("Answer continues. "*30),parse_special=True)+self.eos
        old_e,old=self.run_case(None,raw=raw)
        eng,new=self.run_case("1",raw=raw)
        self.assertEqual(semantic(new),semantic(old))
        self.assertGreater(len(eng.calls),1)
        self.assertEqual(eng.calls[1][0],self.prompt+raw[:8])
        self.assertEqual(sum(len(r["ids"]) for r in eng.receipts),semantic(new)["completion_tokens"])
        self.assertEqual(len(old_e.calls),1)
    def test_natural_eos_exact_cap(self):
        raw=self.bytes("abc")+self.eos
        for flag in (None,"1"):
            engine,events=self.run_case(flag,raw=raw,budget=len(raw))
            self.assertEqual(semantic(events)["finish"],"stop")
            self.assertEqual(len(engine.calls),1)
            self.assertEqual(semantic(events)["completion_tokens"],len(raw))
    def test_stop_string_at_cap_is_terminal(self):
        raw=self.tok.encode("</think>\n\nDone STOP ignored",parse_special=True)+self.eos
        _,old=self.run_case(None,raw=raw,budget=8,sampling={"stop":"STOP"})
        engine,new=self.run_case("1",raw=raw,budget=8,sampling={"stop":"STOP"})
        self.assertEqual(semantic(new),semantic(old))
        self.assertEqual(semantic(new)["finish"],"stop")
        self.assertNotIn("ignored",semantic(new)["content"])
    def test_utf8_and_partial_tag_boundary_extensions(self):
        for text,budget in (("\u4e2dabcde"*10,1),("<xabcdefghij"*10,1)):
            with self.subTest(text=text):
                raw=self.bytes(text)+self.eos
                _,old=self.run_case(None,raw=raw,budget=budget)
                engine,new=self.run_case("1",raw=raw,budget=budget)
                self.assertEqual(semantic(new),semantic(old))
                self.assertEqual(engine.calls[0][1],1)
                self.assertGreater(len(engine.calls),2)
                # Every raw continuation (before the one inserted wrap) resumes exact prefix.
                for ids,cap,_ in engine.calls[1:]:
                    suffix=ids[len(self.prompt):]
                    if self.wrap not in [suffix[i:i+len(self.wrap)] for i in range(len(suffix))]:
                        self.assertEqual(suffix,raw[:len(suffix)])
                        self.assertEqual(cap,1)
    def test_no_room_and_global_budget(self):
        for maximum,budget in ((8,1),(2,1),(12,100)):
            _,old=self.run_case(None,maximum=maximum,budget=budget)
            engine,new=self.run_case("1",maximum=maximum,budget=budget)
            self.assertEqual(semantic(new),semantic(old))
            self.assertLessEqual(semantic(new)["completion_tokens"],maximum)
            self.assertEqual(len(engine.calls),1)
    def test_cancel_and_error_do_not_resume(self):
        engine,events=self.run_case("1",cancel_after=2)
        self.assertEqual(semantic(events)["finish"],"cancel")
        self.assertEqual(len(engine.calls),1)
        with self.assertRaises(ValueError):self.run_case("1",fault="error")
    def test_no_progress_fails_closed(self):
        for fault in ("empty","wrong_done","missing_done","overcap"):
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.run_case("1",fault=fault)
    def test_unsafe_native_args_leave_legacy_requests(self):
        base,_=self.run_case(None)
        for args in ([],SAFE_ARGS+["--mtp-max-t","4"],SAFE_ARGS+["--coupled-draft"],
                     ["--pipeline-windows=2"]+SAFE_ARGS[2:],
                     [x if x!="2" else "4" for x in SAFE_ARGS]):
            engine,_=self.run_case("1",args=args)
            self.assertEqual(engine.calls,base.calls)

    def test_nonneutral_penalties_fall_back_to_legacy(self):
        # The native nonneutral penalty path sets hist_n>0 and disables the qualified pipeline.
        cases={"presence_penalty":(0.5,-0.5),
               "frequency_penalty":(0.5,1.0),
               "repetition_penalty":(0.9,1.1)}
        for key,values in cases.items():
            for value in values:
                with self.subTest(key=key,value=value):
                    with contextlib.redirect_stdout(io.StringIO()):
                        legacy,old=self.run_case(None,sampling={key:value})
                    with contextlib.redirect_stdout(io.StringIO()) as log:
                        candidate,new=self.run_case("1",sampling={key:value})
                    self.assertEqual(candidate.calls,legacy.calls)
                    self.assertEqual(candidate.calls[0][1],256)
                    self.assertEqual(semantic(new),semantic(old))
                    self.assertNotIn("reasoning_native_cap",log.getvalue())

    def test_neutral_penalties_keep_cooperative_cap(self):
        cases=({},{"presence_penalty":0},{"presence_penalty":-0.0},
               {"frequency_penalty":0.0},{"repetition_penalty":1},
               {"repetition_penalty":1.0,"presence_penalty":0.0,"frequency_penalty":0},
               {"penalty_last_n":64})
        for sampling in cases:
            with self.subTest(sampling=sampling):
                with contextlib.redirect_stdout(io.StringIO()):
                    legacy,old=self.run_case(None,sampling=sampling)
                with contextlib.redirect_stdout(io.StringIO()) as log:
                    candidate,new=self.run_case("1",sampling=sampling)
                self.assertEqual(candidate.calls[0][1],8)
                self.assertEqual(legacy.calls[0][1],256)
                self.assertEqual(candidate.calls[1],legacy.calls[1])
                self.assertEqual(semantic(new),semantic(old))
                self.assertIn("reasoning_native_cap",log.getvalue())

    def test_malformed_penalty_values_fail_closed_at_eligibility(self):
        # Service's public request validation is separate: directly exercise the new narrow guard.
        engine=CapEngine(self.tok,[],[])
        with patch.dict(os.environ,{"STRATA_REASONING_NATIVE_CAP":"1"}):
            for key in ("presence_penalty","frequency_penalty","repetition_penalty"):
                for value in (None,False,True,"0",[],{},float("nan"),float("inf")):
                    with self.subTest(key=key,value=repr(value)):
                        self.assertFalse(server.reasoning_native_cap_enabled(engine,{key:value},None))

if __name__=="__main__":unittest.main()
