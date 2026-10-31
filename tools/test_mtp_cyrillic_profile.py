#!/usr/bin/env python3
"""CPU checks only: profile data and server argument forwarding, no GPU/API activity."""
import ast
import copy
import hashlib
import json
import os
import types
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "docs/profiles/mtp-cyrillic.json"
EXPECTED_SHA = "25d7fd1670a2e0ec885868d1718d410a3baab03bceeacf0a156cf93ffe4e1ef4"


def engine_args_only():
    tree = ast.parse((ROOT / "serve/server.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "engine_args")
    # Isolate the actual function without importing/starting the API. Unrelated
    # optional profile/parallel branches are stubbed; their own tests cover them.
    ns = {"layer_split_of": lambda cfg: False, "parallel_args": lambda cfg, args: [],
          "learned_profile_args": lambda cfg, args: args}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "engine_args", "exec"), ns)
    return ns["engine_args"]


class ProfileTests(unittest.TestCase):
    def test_fragment_only_adds_draft_override(self):
        p = json.loads(PROFILE.read_text())
        self.assertEqual(p, {"args": ["--mtp-draft-vocab", "/src/data/draft_vocab_cyrillic.bin"]})

    def test_shortlist_identity(self):
        data = (ROOT / "data/draft_vocab_cyrillic.bin").read_bytes()
        self.assertEqual(len(data), 235852)
        self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED_SHA)
        ids = struct.unpack("<58963i", data)
        self.assertEqual(len(set(ids)), 58963)
        self.assertGreaterEqual(min(ids), 0)
        self.assertLess(max(ids), 248320)

    def test_forwarding_preserves_existing_arguments(self):
        original = {"args": ["--pack", "/model", "--mtp", "/mtp", "--expert-cache", "9900",
                             "--layer-split", "27", "--prefill", "4096", "--spec", "6"]}
        before = copy.deepcopy(original)
        configured = copy.deepcopy(original)
        configured["args"] += json.loads(PROFILE.read_text())["args"]
        result = engine_args_only()(configured)
        self.assertEqual(result, before["args"] + ["--mtp-draft-vocab", "/src/data/draft_vocab_cyrillic.bin"])
        self.assertEqual(original, before)
        self.assertIsNot(result, configured["args"])
        self.assertEqual(result.count("--mtp-draft-vocab"), 1)

    def test_absolute_path_with_spaces_is_one_argument(self):
        args = ["--mtp", "/mtp", "--mtp-draft-vocab", "/some directory/draft.bin"]
        self.assertEqual(engine_args_only()({"args": args}), args)


    def test_effective_environment_preserves_config_overrides(self):
        tree = ast.parse((ROOT / "serve/server.py").read_text())
        names = {"child_env", "hip_visible", "gpu_list", "ordered_gpus"}
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        self.assertEqual({n.name for n in functions}, names)
        fake_os = types.SimpleNamespace(
            environ={"STRATA_ROUTE_TAIL_SKIP": "7", "STRATA_HIP_SWIGLU_FUSED": "1",
                     "INHERITED": "retained", "HIP_VISIBLE_DEVICES": "9"},
            name="posix", path=os.path, pathsep=os.pathsep)
        # Isolate override precedence; HIP guard policy has its own tests.
        ns = {"os": fake_os, "Path": Path, "hip_env_guard": lambda env, cfg: None}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "child_env", "exec"), ns)
        cfg = {"backend": "hip", "gpu": [0, 1], "gpu_order": "as_given", "env": {
            "STRATA_ROUTE_TAIL_SKIP": 0, "STRATA_IQ_MT_MIN": 1,
            "STRATA_HIP_SWIGLU_FUSED": 0, "OTHER": "value", "EMPTY": "", "NONE": None}}
        before = copy.deepcopy(cfg)
        result = ns["child_env"](cfg)
        expected = {"STRATA_ROUTE_TAIL_SKIP": "0", "STRATA_IQ_MT_MIN": "1",
                    "STRATA_HIP_SWIGLU_FUSED": "0", "OTHER": "value", "EMPTY": "",
                    "NONE": "None", "INHERITED": "retained", "HIP_VISIBLE_DEVICES": "0,1"}
        for key, value in expected.items():
            self.assertEqual(result[key], value, key)
        self.assertEqual(cfg, before)


if __name__ == "__main__":
    unittest.main()
