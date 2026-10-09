# Reuse the already published standalone probe

Archive context: the frozen-stack model qualification subsequently completed; see [final qualification report](qsa-reduce12-report.md). The public-source port remains source-reviewed/apply-checked only, without a separate build or GPU qualification. The preparation-time statements below are historical.

## Conclusion

No probe, CMake or production test-macro change is required. The existing source at the exact published head is:

- `bench/gfx906_qsa_query_swizzle_probe.cpp`
- CMake target: `gfx906_qsa_query_swizzle_probe`
- Source URL: https://github.com/0FL01/Strata/blob/1f555de86254cc01ec06882c70f9584c1f09ec39/bench/gfx906_qsa_query_swizzle_probe.cpp
- Existing target wiring: https://github.com/0FL01/Strata/blob/1f555de86254cc01ec06882c70f9584c1f09ec39/CMakeLists.txt#L1545-L1548

The target links `strata_kernels` and the HIP runtime. The probe calls production `qsa_decode_attn_batch`, so the production dispatcher's new reduce12 flag selects A or B without the probe knowing about it. The fixed inputs do not depend on the candidate flag. It runs one checked invocation, three warmups, then event-timed repetitions of the complete batch call including chunk and merge. Its output is the complete `nq * 24 * 256 * sizeof(float)` bytes, without a header or sampled prefix. It checks finite/written outputs, guards, and byte identity between first and final invocation in each process.

The probe uses batches of at most 32 queries. `nq=33` exercises 32+1 dispatch, matching the existing production probe design. Geometry is explicitly checked for 24 query heads, 2 KV heads, head dimension 256 and page size 4.

## Exact future commands (not executed)

Use the exact patched source and the existing qualified compiler/HIP build configuration in a separate checkout. `BUILD` must be its configured `STRATA_HIP_GFX906=ON`, gfx906 build directory. Do not point it at an older qualified8900 archive: the target must link the newly built `strata_kernels` from the exact rebased source. These commands require a separately authorized build/GPU window; no command in this section was run during preparation.

```bash
SRC=/absolute/path/to/separate/patched-checkout
BUILD=/absolute/path/to/its/configured-gfx906-build
sha256sum "$SRC/src/kernels/cuda/qsa_decode_attn.cu"
# Required SHA256: ec0a11258848d6e2bf6ca0bbe463f06eada460a72be10ff5bb4dce065abe3ab0
cmake --build "$BUILD" --target gfx906_qsa_query_swizzle_probe --parallel 2
PROBE="$BUILD/gfx906_qsa_query_swizzle_probe"
test -x "$PROBE"
sha256sum "$PROBE"
```

No `STRATA_GFX906_REDUCE12_PROBE` define, score-only kernel, additional CMake fragment, or new upstream probe file is involved. For multi-configuration generators locate the built executable under its selected configuration directory instead.

The following script is archived as [run-existing-probe.sh](run-existing-probe.sh). From this archive checkout root, invoke `bash bench/results/2026-10-09-gfx906-qsa-reduce12/run-existing-probe.sh` with the absolute executable path, a NEW output directory, and the selected physical GPU ordinal. Run the GPUs sequentially inside the approved exclusive window.

```bash
#!/usr/bin/env bash
set -euo pipefail
PROBE=$(realpath "$1")
OUT=$2
GPU=$3
mkdir "$OUT"  # Fail rather than overwrite an earlier receipt.
OUT=$(realpath "$OUT")
sha256sum "$PROBE" > "$OUT/binary.sha256"
printf 'HIP_VISIBLE_DEVICES=%s\nQUERY_SWIZZLE=1\nLANECELL=0\n' "$GPU" > "$OUT/fixed-environment.txt"

run() {
  local tag=$1 flag=$2 nq=$3 ctx=$4 reps=$5 trace=$6
  shift 6
  printf 'REDUCE12=%s TRACE=%s nq=%s ctx=%s reps=%s\n' \
    "$flag" "$trace" "$nq" "$ctx" "$reps" > "$OUT/$tag.env"
  env -u CUDA_VISIBLE_DEVICES -u ROCR_VISIBLE_DEVICES \
    -u STRATA_GFX906_ATTN_QUERY_SWIZZLE_TRACE \
    HIP_VISIBLE_DEVICES="$GPU" \
    STRATA_GFX906_ATTN_QUERY_SWIZZLE=1 STRATA_ATTN_LANECELL=0 \
    STRATA_GFX906_ATTN_REDUCE12="$flag" \
    STRATA_GFX906_ATTN_REDUCE12_TRACE="$trace" \
    "$PROBE" "$nq" "$ctx" "$reps" "$OUT/$tag.bin" "$@" \
    > "$OUT/$tag.stdout" 2> "$OUT/$tag.stderr"
}

# Separate smoke proves that the new production specialization is actually selected.
# Smoke timing is excluded from ABBA.
run route-smoke 1 32 65536 1 1
grep -q 'strata attn-reduce12: selected=1 query_swizzle=1 kv_mode=1' "$OUT/route-smoke.stderr"

# Each arm is a separate process. Only reduce12 changes between timing arms.
run A1 0 32 65536 50 0
run B1 1 32 65536 50 0
run B2 1 32 65536 50 0
run A2 0 32 65536 50 0
for tag in B1 B2 A2 route-smoke; do cmp "$OUT/A1.bin" "$OUT/$tag.bin"; done
# Each complete nq=32 dump must be 786432 bytes.
test "$(wc -c < "$OUT/A1.bin")" -eq 786432

# Additional full-output parity cases, not the main timing comparison.
run edge1-A 0 1 4 20 0
run edge1-B 1 1 4 20 0
cmp "$OUT/edge1-A.bin" "$OUT/edge1-B.bin"
run edge33-A 0 33 4096 20 0 --masked-pages
run edge33-B 1 33 4096 20 0 --masked-pages
cmp "$OUT/edge33-A.bin" "$OUT/edge33-B.bin"
sha256sum "$OUT"/*.bin > "$OUT/full-output.sha256"

python3 - "$OUT" <<'PY'
from pathlib import Path
import json,re,sys
p=Path(sys.argv[1]); arms={}; inputs=set()
for tag in ['A1','B1','B2','A2']:
    t=(p/f'{tag}.stdout').read_text()
    assert re.search(r'arch=gfx906(?::[^ ]*)? ',t), (tag,'wrong arch')
    assert 'PASS finite_written_guards_and_repeat' in t
    inputs.add(re.search(r'INPUT_FNV1A64=([0-9a-f]+)',t).group(1))
    arms[tag]=float(re.search(r' median_ms=([0-9.]+)',t).group(1))
assert len(inputs)==1, 'input hashes differ'
a=(arms['A1']+arms['A2'])/2
b=(arms['B1']+arms['B2'])/2
r={'process_medians_ms':arms,'A_mean_ms':a,'B_mean_ms':b,
   'component_latency_reduction_pct':100*(a-b)/a,
   'input_fnv1a64':next(iter(inputs)),
   'metric':'full production QSA chunk+merge component latency; not model TPS'}
(p/'abba-summary.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
PY
```

Invocation and cross-device parity:

```bash
bash bench/results/2026-10-09-gfx906-qsa-reduce12/run-existing-probe.sh "$PROBE" /absolute/path/to/new-receipt/gpu0 0
bash bench/results/2026-10-09-gfx906-qsa-reduce12/run-existing-probe.sh "$PROBE" /absolute/path/to/new-receipt/gpu1 1
for tag in A1 B1 B2 A2 edge1-A edge1-B edge33-A edge33-B; do
  cmp "/absolute/path/to/new-receipt/gpu0/$tag.bin" \
      "/absolute/path/to/new-receipt/gpu1/$tag.bin"
done
```

The wrapper deliberately clears conflicting device-visibility selectors for these single-device invocations. If the scheduler provides required isolation, use its assigned visible GPU and preserve that isolation instead of overriding it. Never run this over another process's GPU reservation.

## Limits and minimal publication scope

The existing probe does not print the reduce12 environment value or enforce selection itself. The wrapper records the value per arm, and the separate production trace-smoke proves selection. `STRATA_GFX906_ATTN_QUERY_SWIZZLE_TRACE` is removed rather than set to `0`: its existing parsing is based on presence. Reduce12 trace requires exactly `1`, so `0` disables it in timing arms.

The existing probe has no raw-score output. Preserve the previously completed raw-score micro hashes/artifacts in a separate benchmark receipt; do not add its diagnostic kernel or test macro to the production patch merely to reproduce that check. The production full-output probe and source/ISA evidence are separate checks with separate scopes.

These commands describe a future clean-rebase component check; they do not retroactively turn frozen-stack measurements into clean-rebase validation. Whole-model 4K/200K/API qualification remains unfinished as of this preparation. No publication, build or GPU execution was performed here.
