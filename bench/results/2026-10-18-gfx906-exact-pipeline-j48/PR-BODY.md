## Dependent draft — builds on #2966

This is a supplement to #2966, not a replacement or a claim that its existing optimizations are new. Until #2966 lands, the main-branch diff includes its commits. Review the incremental commits starting at `744243d293d63c8647f83ece6b5621f2f84f8747`.

The new work adds exact-F16 workspace reuse, shape-aware preparation around the existing decode pipeline, and an opt-in, guarded J48 MMQ hint for local full-routing gfx906 prefill. The existing pipeline mode 2 itself is not introduced by this PR.

### Measured whole operating profile

Two Radeon Pro VII 16 GiB (gfx906), same model and expert-cache capacity; 65,536 prompt / 1,024 generated tokens, six interleaved pairs, all runs retained.

| | Baseline | Candidate | Paired change | 95% paired-log t interval |
|---|---:|---:|---:|---:|
| PP, t/s | 644.6466 | 649.5473 | +0.7585% | −0.7457% to +2.2855% |
| TG, t/s | 55.2240 | 61.6476 | +11.6318% | +11.4085% to +11.8555% |

All 12 runs matched all 1,024 reference output token IDs. All six TG pairs were positive. This comparison includes pipeline/reserve configuration changes; it is not an isolated J48 gain or a comparison with identical speculative work. Zero PP regression is **not** established.

### Correctness and incremental checks
- J48 held-out component replay: 35 vectors, two campaigns, both GPUs; exact output/canary checks.
- 64K accepted0705→J48 ABBA: PP +0.6716%, TG +0.1926%; all four outputs exact.
- 200K/256 single pair: PP 605.4084→612.5657, TG 54.0826→54.1112; exact output. Preliminary.
- 8K repeat ON/OFF/OFF/ON: exact outputs; PP +1.5043%, TG −0.2820%. An initial 8K PP slowdown is retained and unexplained; it did not repeat.

### Why this stays Draft
- CUDA and other HIP-device builds/runtimes remain unverified. Shared host code changes include Product, verify capture, and prompt preparation ordering; this does not claim non-gfx906 host execution is untouched.
- Existing HIP build prerequisites overlap #2020, #2460 and #2459/#3083. They are documented as a reproducibility patch, **not proposed again as optimization code**. The published source is not claimed to build standalone on gfx906 without those prerequisites.
- Do not combine with #1457 workspace-lifetime changes without fresh analysis/tests.
- #3078's void cudaFree wrapper conflicts with checked frees in the inherited HC code; it is not imported.
- Fixed synthetic fixtures and token equality do not establish all model-quality, vision or agent-session behavior.
- No production deployment.

[Full report, per-run results, hashes, benchmark script and prerequisites](https://github.com/0FL01/Strata/tree/64a33632164059477146ebec0eaf2487c2ab6797/bench/results/2026-10-18-gfx906-exact-pipeline-j48)

The source and raw local test artifacts are preserved on the MI50 host; the earlier accepted +11.48% TG result is retained as a rollback.
