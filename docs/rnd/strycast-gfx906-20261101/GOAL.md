# Goal: evidence-led Strycast transfer to gfx906

Status: active R&D, 2026-11-01. Branch: `rnd/strycast-gfx906-20261101`.
Base: `57e80921fb4528aeaf190d54fd2c5dfa28052341`.
Upstream reference: Strycast `36fc59743b6b400d9ecfd303162bd156044b41f5`, MIT.
Retain relevant copyright/license notices if copying code. Inspect source first; do not run upstream programs wholesale.

## Objective and operating constraints

Improve real cold prefill (PP), generation (TG), TTFT and total time on the existing gfx906 FlashNext deployment without correctness or workload regressions.
The user authorized stopping production, iterative tests, and committing/pushing the work; promote a demonstrated gain without regressions to main immediately. Production remains stopped during R&D; promotion does not implicitly authorize deploying a new binary.
One research branch holds plans, code, tests and negative findings. Preserve exact rollback state. Public records omit host paths and credentials.

## Baseline frozen before stop

Fresh health: loaded, idle, queued=0. Original production container stopped at 2026-11-01T11:05:39Z; subsequent independent read confirmed stopped and no running containers.
Native SHA256: `731cbb6c886d4631e2ee71c5dc633de36b639288fc3a1acf30652a6518ac8180`.
Config SHA256: `961da921458099c727dc22c7b7ad769e046f270d27342c0be902ee128d6dc612`.
Keep existing model, full verifier, API overlay and static MTP shortlist (58,963 rows).
Cache: prompt checkpoints 32, interval 16,384 tokens; conversation slots 8, budget 16,384 MiB, minimum host free 8,192 MiB.
Private exact config, container inspection, native arguments, API source hashes and live state are retained remotely.
The baseline includes ALL 48 config environment overrides, especially explicit GDN_HEAD=1/GDN_PP=2. Docker Env alone is not the native environment: derive and verify the full server child_env(cfg) contract, device visibility and library settings before running.
Current main source and installed native are different provenance. Rebuilt control and candidate must share source/toolchain/configuration except the intended patch; additionally compare the actual installed baseline honestly.

## Copied research plan, with source-based refinements

1. **Streamed expert MMQ compact tile scheduling.** Existing groups of at most 16 experts use max_rows. Measure actual expert formats, MMQ eligibility, selected I/J/K (including J48), counts and empty CTAs per device/projection. Important correction: the pinned upstream scheduler already exits empty expert tiles before GEMM, after shared-id initialization/barrier. There are no padded GEMM FLOPs to reclaim; only empty-CTA scheduling/init overhead. Quantize-once, scatter and fused gate/up already exist. Cheapest candidate is a by-value 17-entry tile prefix for a group, no allocation/upload/synchronization. Compare its decode overhead against empty-CTA cost first. Do not force a negligible optimization.
2. **MoE combine -> HC fusion.** Existing combine materializes an intermediate consumed by HC. HC write plus following norm already fused. Investigate only the remaining gap, preserving weighted reduction order, tails/scales, peer/CPU contributions, consumers and overlap. Profile to bound possible gain.
3. **Request-aware MTP shortlist.** Existing static 58,963 shortlist is the baseline, not the former 106,299 rows. Strycast uses a base table plus rare/special slots and recent acceptance/misses. Track prompt and committed generated tokens, not rejected drafts. Measure row gathering, updates, fallback, acceptance, TTFT and memory. Full verifier remains unchanged. Keeping a full draft head may erase memory savings.
4. **GDN layout/register work only if profiled.** Existing code already has LDS padding, register pipelining and q/k reuse. Preserve actual runtime dispatch, and do not assume wave32 paths qualify on gfx906 wave64.

The claimed ~3,000 PP upstream is another model/hardware/workload; incremental cached prefill is not cold long-context prefill. Do not transfer that number.
Previously tested ring384->512 and prefill4096->8192 were negative; the latter reduced overlap and diverged in tokens. No blind reruns. Avoid duplicating existing gate/up, quantization/scatter, GDN pipeline and cache mechanisms.

## Iteration protocol

- Read and record exact source/dependency/build provenance, runtime dispatch and model layouts.
- Cheap source and host-counter falsification before invasive code or long GPU sweeps.
- Profile the relevant phase and upper-bound total benefit. A failed idea advances to the next grounded gap.
- New behavior opt-in; default path unchanged. Narrow gfx906 guards; no silent CUDA/HIP/SYCL behavior change.
- Owned lock, one GPU experiment at a time, process/container receipts, cleanup only owned jobs. Production stays OFF.
- Same effective native environment, model, expert cache, context, prompt/token IDs, work count and sampling. Record intended differences explicitly.
- Correctness gate: exact intermediate state/logits where observable, output token IDs, generated work, MTP acceptance, undo/rebranch and checkpoint lifecycle. Quality failure rejects candidate immediately.
- Focused tests cannot establish the full gate. Matched cold 2K/8K/64K and generation 1K/4K, Russian/code/general cases, mirrored run order and repeats; report PP/TG, TTFT, full wall, VRAM/host memory and variance.
- Reject mixed or unsupported speedups for main. Build/test every touched backend before review or explicitly mark unavailable qualification as blocking.
- Independent review of harness, provenance, diffs, correctness and measurements before promotion.
- Keep raw evidence private and publish sanitized reproducible method, results, limitations and failures. Never label absent CI as green.
- Before promotion verify fresh main and revalidate any integration changes; preserve rollback, commit/push and verify remote refs/checks.

## Progress

- Fresh production snapshot and authorized stop completed.
- Empty-CTA early return found: corrected expected benefit before writing scheduler code.
- Goal/protocol is committed before GPU experiments. Full environment receipt, baseline harness and performance evidence follow in this branch.
