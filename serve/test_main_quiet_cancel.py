import unittest
import io,queue,threading
from unittest import mock
from serve import server
class QuietWaitPolicy(unittest.TestCase):

    def test_expired_silence_is_not_a_heartbeat(self):
        engine = object.__new__(server.StrataEngine)
        engine.proc = mock.Mock()
        engine.proc.poll.return_value = None
        engine.proc.stdin = io.StringIO()
        engine.lines = mock.Mock()
        engine.can_stop, engine.silence_s, engine.log_path = (True, 10, None)
        now = [0.0]

        def clock():
            now[0] += 0.001
            return now[0]

        def get(timeout):
            now[0] += timeout
            raise queue.Empty
        engine.lines.get.side_effect = get
        with mock.patch.object(server.time, 'monotonic', clock):
            gen = engine.generate([], 10, {}, threading.Event())
            with self.assertRaises(server.EngineSilent):
                next(gen)
        engine.proc.kill.assert_called_once()
        self.assertNotIn('STOP', engine.proc.stdin.getvalue())

    def test_polling_keeps_ten_second_heartbeats(self):
        for control in (False, True):
            with self.subTest(control=control):
                engine = object.__new__(server.StrataEngine)
                engine.proc = mock.Mock()
                engine.proc.poll.return_value = None
                engine.proc.stdin = io.StringIO()
                engine.lines = mock.Mock()
                engine.can_stop, engine.silence_s = (True, 0)
                engine._ctl_mode = 'solo'
                engine._send = mock.Mock()
                now = [0.0]
                waits = []

                def get(timeout):
                    waits.append(timeout)
                    if now[0] >= 21.0:
                        return 'DONE 0 1 1 0 length'
                    now[0] += timeout
                    raise queue.Empty
                engine.lines.get.side_effect = get
                cancel = threading.Event()
                with mock.patch.object(server.time, 'monotonic', lambda: now[0]):
                    gen = engine._control(cancel, lambda t: None) if control else engine.generate([1], 1, {}, cancel)
                    heartbeats = list(gen)
                self.assertEqual(heartbeats, [None, None], 'a quiet 21 seconds emits two heartbeats, not 42')
                self.assertTrue(all((0 < wait <= 0.5 for wait in waits)), 'cancellation uses bounded blocking waits')
                engine._send.assert_not_called()
                self.assertNotIn('STOP', engine.proc.stdin.getvalue())

class CancelPoll(unittest.TestCase):
 def test_stop_after_half_second_and_next_done(self):
  for control in (False,True):
   with self.subTest(control=control):
    e=object.__new__(server.StrataEngine);e.proc=mock.Mock();e.proc.poll.return_value=None;e.proc.stdin=io.StringIO()
    e.can_stop=True;e.silence_s=0;e.last=None;e._ctl_mode='solo';e.lines=mock.Mock()
    cancel=threading.Event();now=[0.0];calls=[];sent=[]
    def get(timeout):
     calls.append(timeout)
     if len(calls)==1:now[0]+=timeout;cancel.set();raise queue.Empty
     return 'DONE 0 1 1 0 cancel'
    e.lines.get.side_effect=get;e._send=lambda x:sent.append((x,now[0]))
    with mock.patch.object(server.time,'monotonic',lambda:now[0]):
     rows=list(e._control(cancel,lambda t:None) if control else e.generate([1],10,{},cancel))
    self.assertLessEqual(calls[0],.5);self.assertEqual(rows,[])
    if control:self.assertEqual(sent,[('STOP',.5)])
    else:self.assertEqual(e.proc.stdin.getvalue().count('STOP'),1)
