"""CPU-only ownership regression: real preparation/cache code, fake encoder I/O."""
import collections
import pathlib
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock
from serve import server
from serve.frontend import ChatTemplate

class VisionCacheLifetime(unittest.TestCase):
    def test_concurrent_prepare_keeps_sources_until_combined_copy(self):
        self.exercise()

    def test_waiting_prepare_proceeds_after_copy_exception(self):
        self.exercise(fail_a=True)

    def exercise(self, fail_a=False):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            vision = object.__new__(server.Vision)
            vision.dir = directory
            vision.cache = collections.OrderedDict()
            vision.lock = threading.Lock()
            vision.normalize = lambda data: data
            vision.load = lambda source: source.encode()
            pending = []
            class Pipe:
                def write(self, line):
                    op, image, output = line.split()
                    if op != "ENC":
                        raise AssertionError(op)
                    payload = b"embed:" + (directory / image).read_bytes()
                    (directory / output).write_bytes(payload)
                    pending.append("OK 1")
                    return len(line)
                def flush(self):
                    pass
            vision.proc = SimpleNamespace(stdin=Pipe())
            vision._readline = lambda *args: pending.pop(0)
            tok = server.ByteTokenizer()
            svc = server.Service(server.MockEngine(tok, "ok", max_context=8192), tok,
                                 ChatTemplate(pathlib.Path(__file__).with_name("chat_template.jinja")))
            svc.vision = vision
            a_released, b_finished = threading.Event(), threading.Event()
            real_lock = threading.Lock()
            class Fifo:
                def acquire(self, *args, **kwargs):
                    return real_lock.acquire(*args, **kwargs)
                def release(self):
                    real_lock.release()
                    if threading.current_thread().name == "prepare-A":
                        a_released.set()
                        if not b_finished.wait(10):
                            raise TimeoutError("B did not finish after A released the FIFO")
            svc.fifo = Fifo()
            results, errors = {}, {}
            def prepare(label, sources):
                try:
                    if label == "B" and not a_released.wait(10):
                        raise TimeoutError("A did not release the FIFO")
                    messages = [{"role":"user", "content":[{"type":"image", "source":s} for s in sources]}]
                    svc.prepare(messages, None, {"enable_thinking":False}, 10, cancel=threading.Event())
                    path = svc.embeddings.path
                    results[label] = {"payload":path.read_bytes(), "path":str(path),
                                      "keys":list(svc.embeddings.keys)}
                except BaseException as exc:
                    errors[label] = (type(exc).__name__, str(exc))
                finally:
                    path = getattr(svc.embeddings, "path", None)
                    if path is not None:
                        path.unlink(missing_ok=True)
                    if label == "B":
                        b_finished.set()
            a_sources = ["image-A"]
            b_sources = ["image-B-" + str(i) for i in range(64)]
            original_write = server.write_temporary
            def write(path, parts):
                if fail_a and threading.current_thread().name == "prepare-A":
                    path.write_bytes(b"partial")
                    raise RuntimeError("injected A copy failure")
                original_write(path, parts)
            with mock.patch.object(server, "combined_embeddings_path",
                                   side_effect=lambda root, size: directory / ("combined-" + threading.current_thread().name)), \
                 mock.patch.object(server, "write_temporary", side_effect=write):
                threads = [threading.Thread(target=prepare, args=("A", a_sources), name="prepare-A", daemon=True),
                           threading.Thread(target=prepare, args=("B", b_sources), name="prepare-B", daemon=True)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(15)
                self.assertFalse(any(thread.is_alive() for thread in threads), "bounded ownership test hung")
            self.assertEqual(errors, {"A": ("RuntimeError", "injected A copy failure")} if fail_a else {}, errors)
            if not fail_a:
                self.assertEqual(results["A"]["payload"], b"embed:image-A")
                self.assertNotEqual(results["A"]["path"], results["B"]["path"])
                self.assertEqual(len(results["A"]["keys"]), 1)
            self.assertEqual(results["B"]["payload"], b"".join(b"embed:" + s.encode() for s in b_sources))
            self.assertEqual(len(results["B"]["keys"]), 64)
            self.assertLessEqual(len(vision.cache), 64)
            self.assertFalse(list(directory.glob("combined-*")))

class PrepareOwnership(unittest.TestCase):
    def make(self, directory, cancel, mode):
        tok = server.ByteTokenizer()
        svc = server.Service(server.MockEngine(tok, "ok", max_context=8192), tok,
                             ChatTemplate(pathlib.Path(__file__).with_name("chat_template.jinja")))
        class Lock:
            def __init__(self):
                self.inner = threading.Lock()
                self.acquired = self.released = 0
            def acquire(self, *a, **kw):
                got = self.inner.acquire(*a, **kw)
                if got:
                    self.acquired += 1
                return got
            def release(self):
                self.released += 1
                self.inner.release()
        svc.fifo = Lock()
        source = directory / "cached.sve"
        source.write_bytes(b"embedding-payload")
        def encode_all(images, event):
            if mode == "cancel":
                event.set()
            return [(source, 1)]
        svc.vision = SimpleNamespace(encode_all=encode_all, dir=directory)
        return svc, source

    def test_normal_copy_holds_turn_until_finished(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=pathlib.Path(tmp);cancel=threading.Event()
            svc,source=self.make(directory,cancel,"normal")
            combined=directory/"combined.sve"
            original=server.write_temporary
            def write(path,parts):
                self.assertTrue(svc.fifo.inner.locked())
                original(path,parts)
            with mock.patch.object(server,"combined_embeddings_path",return_value=combined), mock.patch.object(server,"write_temporary",side_effect=write):
                svc.prepare([{"role":"user","content":[{"type":"image","source":"fake"}]}],None,{"enable_thinking":False},10,cancel=cancel)
            self.assertEqual(combined.read_bytes(),source.read_bytes())
            self.assertEqual((svc.fifo.acquired,svc.fifo.released),(1,1))
            self.assertFalse(svc.fifo.inner.locked())
            svc.drop_embeddings()
            self.assertFalse(combined.exists());self.assertTrue(source.exists())

    def test_cancel_and_budget_refusal_release_without_combining(self):
        for mode in ("cancel","budget"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cancel=threading.Event();svc,source=self.make(pathlib.Path(tmp),cancel,mode)
                with mock.patch.object(server,"combined_embeddings_path",side_effect=AssertionError("combined before refusal")):
                    with self.assertRaises(server.ClientGone if mode=="cancel" else ValueError):
                        svc.prepare([{"role":"user","content":[{"type":"image","source":"fake"}]}],None,{"enable_thinking":False},100000 if mode=="budget" else 10,cancel=cancel)
                self.assertEqual((svc.fifo.acquired,svc.fifo.released),(1,1))
                self.assertTrue(svc.fifo.acquire(blocking=False));svc.fifo.release()
                self.assertIsNone(svc.embeddings.path)
                self.assertTrue(source.exists())

    def test_copy_error_leaves_owned_partial_for_caller_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=pathlib.Path(tmp);svc,source=self.make(directory,threading.Event(),"error")
            combined=directory/"combined.sve"
            def fail(path,parts):
                self.assertTrue(svc.fifo.inner.locked())
                path.write_bytes(b"partial")
                raise OSError("injected copy error")
            with mock.patch.object(server,"combined_embeddings_path",return_value=combined),mock.patch.object(server,"write_temporary",side_effect=fail):
                with self.assertRaisesRegex(OSError,"injected"):
                    svc.prepare([{"role":"user","content":[{"type":"image","source":"fake"}]}],None,{"enable_thinking":False},10,cancel=threading.Event())
            self.assertEqual((svc.fifo.acquired,svc.fifo.released),(1,1))
            self.assertEqual(svc.embeddings.path,combined)
            svc.drop_embeddings();self.assertFalse(combined.exists());self.assertTrue(source.exists())
            self.assertTrue(svc.fifo.acquire(blocking=False));svc.fifo.release()

    def test_text_only_never_acquires_image_turn(self):
        tok=server.ByteTokenizer()
        svc=server.Service(server.MockEngine(tok,"ok",max_context=8192),tok,ChatTemplate(pathlib.Path(__file__).with_name("chat_template.jinja")))
        svc.fifo=mock.Mock()
        svc.prepare([{"role":"user","content":"hello"}],None,{"enable_thinking":False},10,cancel=threading.Event())
        svc.fifo.acquire.assert_not_called();svc.fifo.release.assert_not_called()

from serve import test_server as server_tests
class CurrentVisionCachePolicy(server_tests.VisionCacheEviction):
    def make(self, directory):
        vision=super().make(directory)
        vision._readline=lambda *args: vision.proc.stdout.readline()
        return vision
