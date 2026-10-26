"""CPU-only sampled admission tests using the existing actual Service/native-cap simulation."""
import contextlib
import io
import os
import unittest
from unittest.mock import patch
from serve import server
from serve import test_reasoning_native_cap as base

PROFILE = dict(temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, seed=12345,
               repetition_penalty=1.0, presence_penalty=0.0, frequency_penalty=0.0)
FLAG = "STRATA_REASONING_NATIVE_CAP_SAMPLED"


class SampledNativeCap(base.NativeCap):
    # Re-exercise the existing wrap, early-close, EOS, UTF8, cancellation/error,
    # malformed DONE, output-budget, tool, argv and penalty invariants as sampled.
    def run_case(self, flag, *args, sampling=None, **kwargs):
        with patch.dict(os.environ, {FLAG: "1"}):
            return super().run_case(flag, *args, sampling={**PROFILE, **(sampling or {})}, **kwargs)

    def test_effective_sampling_forwarded_each_segment(self):
        for seed in (12345, 23456, 34567):
            with self.subTest(seed=seed), contextlib.redirect_stdout(io.StringIO()):
                engine, events = self.run_case("1", sampling={"seed": seed})
                self.assertEqual(engine.calls[0][1], 8)
                self.assertEqual(len(engine.calls), 2)
                for _, _, sampling in engine.calls:
                    for key, value in {**PROFILE, "seed": seed}.items():
                        self.assertEqual(sampling[key], value)
                    wire = server.StrataEngine.sampling_keys(sampling)
                    self.assertIn(" temperature=1.0", wire)
                    self.assertIn(" top_p=0.95", wire)
                    self.assertIn(" top_k=20", wire)
                    self.assertIn(" seed=" + str(seed), wire)
                    self.assertNotIn("penalty_", wire)
                self.assertEqual(base.semantic(events)["finish"], "stop")


class SampledAdmission(base.NativeCap):
    # Avoid inheriting/rerunning the base tests here; load_tests below selects only
    # this class's new tests. The other subclass intentionally inherits all 13.
    def admitted(self, sampling, base_flag="1", sampled_flag="1", engine=None, embeddings=None):
        if engine is None:
            engine = base.CapEngine(self.tok, [], [])
        env = dict(os.environ)
        for key, value in (("STRATA_REASONING_NATIVE_CAP", base_flag), (FLAG, sampled_flag)):
            env.pop(key, None)
            if value is not None:
                env[key] = value
        with patch.dict(os.environ, env, clear=True):
            return server.reasoning_native_cap_enabled(engine, sampling, embeddings)

    def test_exact_flags_and_seed_profile(self):
        self.assertTrue(self.admitted(PROFILE))
        for flag in (None, "", "0", "true", "11"):
            self.assertFalse(self.admitted(PROFILE, base_flag=flag))
            self.assertFalse(self.admitted(PROFILE, sampled_flag=flag))
        invalid = {
            "temperature": (None, False, "1", 0.7, float("nan"), float("inf")),
            "top_p": (None, True, "0.95", 1.0, 0.9),
            "top_k": (None, True, "20", 20.0, 0, 64),
            "min_p": (None, False, "0", 0.1),
            "seed": (None, True, "12345", 12345.0, 0, -1, 1, 45678),
        }
        for key, values in invalid.items():
            # None temperature retains historical greedy admission; it cannot select
            # a sampled GEN because sampling_keys sends temperature only when >0.
            for value in values:
                if key == "temperature" and value is None:
                    continue
                with self.subTest(key=key, value=repr(value)):
                    self.assertFalse(self.admitted({**PROFILE, key: value}))
            if key != "temperature":
                missing = dict(PROFILE)
                del missing[key]
                self.assertFalse(self.admitted(missing))

    def test_unsafe_engine_profiles(self):
        engine = base.CapEngine(self.tok, [], [])
        engine.batch = 1
        self.assertFalse(self.admitted(PROFILE, engine=engine))
        engine.batch = 0
        self.assertFalse(self.admitted(PROFILE, engine=engine, embeddings="present"))
        for spawn in (None, (), ("x", None), ("x", [1]), ("x", base.SAFE_ARGS + ["--coupled-draft"])):
            engine.spawn = spawn
            self.assertFalse(self.admitted(PROFILE, engine=engine))

    def test_sampled_flag_absent_actual_service_legacy(self):
        for sampled_flag in (None, "", "0", "true"):
            env = dict(os.environ)
            env.pop(FLAG, None)
            if sampled_flag is not None:
                env[FLAG] = sampled_flag
            with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(io.StringIO()) as log:
                legacy, old = self.run_case(None, sampling=PROFILE)
                candidate, new = self.run_case("1", sampling=PROFILE)
            self.assertEqual(candidate.calls, legacy.calls)
            self.assertEqual(candidate.calls[0][1], 256)
            self.assertEqual(base.semantic(new), base.semantic(old))
            self.assertNotIn("reasoning_native_cap", log.getvalue())

    def test_unsupported_sampled_profile_actual_service_legacy(self):
        for change in ({"seed": 1}, {"top_p": 0.9}, {"temperature": 0.7}, {"presence_penalty": 1.5}):
            with contextlib.redirect_stdout(io.StringIO()), patch.dict(os.environ, {FLAG: "1"}):
                sampling = {**PROFILE, **change}
                legacy, old = self.run_case(None, sampling=sampling)
                candidate, new = self.run_case("1", sampling=sampling)
            self.assertEqual(candidate.calls, legacy.calls)
            self.assertEqual(candidate.calls[0][1], 256)
            self.assertEqual(base.semantic(new), base.semantic(old))

    def test_greedy_admission_unchanged_with_second_flag(self):
        for sampling in ({}, {"temperature": None}, {"temperature": 0}, {"temperature": 0.0}):
            for flag in (None, "", "0", "1"):
                self.assertTrue(self.admitted(sampling, sampled_flag=flag))


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromTestCase(SampledNativeCap)
    for name in SampledAdmission.__dict__:
        if name.startswith("test_"):
            suite.addTest(SampledAdmission(name))
    return suite


if __name__ == "__main__":
    unittest.main()
