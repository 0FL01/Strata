#!/usr/bin/env python3
"""Public CPU-only checks. Uses no original prompt, model, network or GPU."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CXX = os.environ.get('CXX', 'c++')

def run(argv, **kwargs):
    subprocess.run(argv, check=True, timeout=120, **kwargs)

with tempfile.TemporaryDirectory(prefix='protected-cache-public-cpu-') as name:
    tmp = Path(name)
    includes = ['-I' + str(ROOT/'runtime/include'),
                '-I' + str(ROOT/'runtime/include/strata/program')]
    for source in ('coverage_test.cpp', 'test_conversation_memory_budget.cpp',
                   'test_checkpoint_metadata.cpp', 'runtime_contract.cpp',
                   '../runtime-v2/tests/recent_retention_contract.cpp'):
        binary = tmp / Path(source).stem
        run([CXX, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror',
             '-pedantic', '-pthread', '-DCOVERAGE_WITH_BUDGET_TESTS',
             *includes, str(ROOT/'tests'/source), '-o', str(binary)])
        run([str(binary)])
    for version in ('replay', 'replay-v2'):
        protocol = tmp/version
        shutil.copytree(ROOT/version, protocol)
        # Deliberately generated public test data; never the original replay prompt.
        (protocol/'prompt-65536.ids.json').write_text(json.dumps(list(range(65536))))
        run([sys.executable, '-B', str(protocol/'test_cpu.py')])
print('PASS: public CPU/metadata/protocol rerun; synthetic seed; no GPU execution')
