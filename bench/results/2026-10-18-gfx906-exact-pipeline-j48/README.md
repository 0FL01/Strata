# Draft: gfx906 exact decode pipeline and prefill preparation

Status: Draft supplement; qualification limits below remain open. Depends on the existing combined gfx906 work in upstream PR #2966. Publication still needs a clean public-base diff review.

## What changes
- Exact decode pipeline and shape-aware preparation.
- Reuse of the existing prefill workspace for exact F16 preparation.
- Opt-in, shape- and device-guarded J48 hint for local full-routing gfx906 expert prefill.
- No quantization or approximation introduced by J48.

## Direct whole-bundle result
Two Radeon Pro VII 16 GiB, gfx906, ROCm 7.14. Same model, 65536 input tokens and 1024 generated tokens, six interleaved pairs. Compare stable binary 891bfedf against candidate cc78113d. All 12 outputs match the fixed reference token IDs exactly.

| Metric | Baseline t/s | Candidate t/s | Paired change | 95% paired-log t interval |
|---|---:|---:|---:|---:|
| PP | 644.6466 | 649.5473 | +0.7585% | -0.7457% to +2.2855% |
| TG | 55.2240 | 61.6476 | +11.6318% | +11.4085% to +11.8555% |

Rates are pooled tokens/time. Changes and intervals use six paired log ratios. All runs retained, including outliers. Three PP pairs positive and three negative; all six TG pairs positive. This does not establish zero PP regression. The comparison includes pipeline mode and reserve changes; it is a whole operating-profile result, not an isolated J48 result or identical speculative work.

## J48 incremental checks
Against protected accepted0705:
- 64K ABBA: PP648.4533→652.8085 (+0.6716%); TG61.6020→61.7206 (+0.1926%). All four1024-token outputs exact. Only two pairs.
- 200K single pair: PP605.4084→612.5657 (+1.1822%); TG54.0826→54.1112 (+0.0528%). Both256-token outputs exact. Preliminary.
- 8K smoke: all256 IDs exact, but first J48-on run slowed PP494→418t/s. Cause unresolved and result retained.
- Held-out component replay:35 vectors, two campaigns, both GPUs; bitwise output and canary checks passed. Component latency gains are not model-level PP gains.

## Scope and remaining limits
- J48 is opt-in and requires gfx906/wave64 plus exact local full-routing shapes and layout checks.
- Other-device runtime validation has not been performed.
- Fixed synthetic fixtures do not establish model quality or all agent/vision behavior.
- The 8K slowdown needs diagnosis before recommending J48 universally.
- Review shared verify/generate changes for other-device safety before publication.
- Do not stack upstream #3078/#3083 compatibility changes blindly; checked cudaFree semantics need review.
- No production deployment performed.

## Reproduction and retained artifacts
Everything below is relative to /home/radneon/strata/rnd-next-20261017:
- Source: hc-j48-prefill-candidate-v1-2-source
- Executable: hc-j48-prefill-normal-v1-build/strata
- Scripts/logs: hc-j48-prefill-normal-v1-assets/{build.py,bench.py}
- Minimal source delta over combined candidate: hc-j48-prefill-normal-v1-assets/combined-delta.patch
- Raw commands, inspection, stdout, stderr, tokens, results: hc-j48-prefill-normal-v1-tests/{smoke,abba64,final64,long200k}
- Protected previous result: KEEP-best-gfx906-tg-11p48-20261018/accepted0705-source-binary-proof.tar.gz

Candidate SHA256: cc78113d53e5eb89146c1c45fccacef47cd89cba3fa39f7f4b59927c7a384b58
Source delta SHA256: cf78f12968388ef9ba26ef30c2fd6844b099e7b3ff82e8518d9881030598e4a4

The benchmark script owns its exact Docker container and removes it after completion. It requires the existing local model/runtime/image and an exclusive GPU benchmark lock. Run a new campaign only with an unused output destination; do not overwrite recorded runs.

## Publication review (18:48 UTC)
The actual delta over local combined candidate is ten files. Shared effects include a Product field, capture_all refactoring, and prompt-window construction moved before eager preparation even when the feature is OFF. CUDA/non-gfx906 builds and runtimes are unverified. Unconditional source-local experimental build definitions are present, while runtime opt-in remains OFF. Full composition with PR #1457 region livespans is unsupported.
Public #2966 head is 744243d293d63c8647f83ece6b5621f2f84f8747. All nine existing changed code files match the local combined base except CMakeLists.txt: local base additionally contains the four-line PR #2460 GGML_USE_HIP definition for strata_mmq_w4a4. Do not present that compatibility hunk as novel or silently omit this baseline difference. Publication needs explicit prerequisite handling against #2460/#3083, without importing #3078's incompatible void cudaFree wrapper.
Short8k on/off/off/on repeat launched18:49 UTC, binary unchanged, to test whether the initial slowdown repeats; retain initial measurement regardless of outcome.

## 18:59 UTC: short8k repeat complete
ON/OFF/OFF/ON, all4 outputs exact256IDs. {"off": {"pp_tps": 488.84990183617094, "tg_tps": 64.63830324453983}, "on": {"pp_tps": 496.2036664072178, "tg_tps": 64.4560263866858}, "pp_delta_pct": 1.5042990790067323, "tg_delta_pct": -0.2819951154417355, "same_tokens": true, "pairs": 2}
Initial 418t/s J48-on PP slowdown did not repeat; its cause remains unknown and original result retained. Do not label it fixed or discard it. Both repeat PP pairs positive. TG one positive/one negative with only256 tokens. No more GPU jobs running.
