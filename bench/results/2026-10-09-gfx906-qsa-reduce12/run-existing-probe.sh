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
