# Iteration log

## Baseline and applicability (2026-11-01)

- Production remains stopped as requested. Exact rollback snapshots are retained privately.
- The installed native is SHA256 `731cbb6c886d4631e2ee71c5dc633de36b639288fc3a1acf30652a6518ac8180`.
- A fresh rebuild of the branch base is `547083bf5338ddb6c61fa3fea4612a0ed95c320ea86ee81a04955d2236cf7910`.
- The actual installed binary's historical build receipt was recovered. Runtime environment flags alone do not prove compiled support: a first default build omitted HC exact/N4 support and used different quant/portable options. It was not benchmarked as the matched control.
- Corrected build uses HC F16 exact, BF16 N4 and BF16 clone ON; KQUANTS/Q6K ON; portable OFF. CPU cached options were explicitly reconciled. An independent per-target review found no semantic compiler-option differences across 208 common production object targets. Source and binary hashes still differ, so provenance is kept separate.
- Dependency is the clean pinned llama.cpp `3cf03257f219afbe7334045ff7c6a06ac68c627d`.
- All 48 actual expert layers have GU/down type 42 (Q2_0). The earlier Q4_0 request concerned the DFlash draft experiment, not a replacement of this verifier.
- All 48 configuration environment overrides are included in 56 effective native keys, derived from the live server's environment function. Tests use explicit working directory and `env -i`; the API credential is omitted in network-isolated native tests.
- Cache configuration remains 32 checkpoints / interval 16K, 8 conversation slots / 16 GiB budget / 8 GiB host free floor, and draft shortlist 58,963.

### Bounded installed/rebuilt diagnostic

One cold 2,048-input / 128-output pair, identical token IDs and fixed greedy work:

| Control | PP tok/s | TG tok/s | TTFT s | Request wall s | MTP accepted/proposed |
|---|---:|---:|---:|---:|---:|
| Installed | 299.92 | 73.11 | 7.071 | 8.592 | 59/65 |
| Matched rebuild | 301.58 | 73.25 | 7.033 | 8.551 | 59/65 |

Both admitted 9,399 primary and 18,018 total expert slots, prefill cap 4,096 and two stages. Token SHA256: `1c19920e8bbd57599dd27b43e2104a788beb7074d819550c914b21d1317a4805`.
EOS was deliberately suppressed in both arms to ensure identical requested work.
These are baseline sanity checks, NOT a speedup claim, full correctness qualification or promotion evidence. The native reports slightly different decode cache lookup totals despite equal tokens/MTP counters; future same-build comparisons must retain those counters rather than assume equal internal work from token equality alone.

## Iteration 1: measure MMQ empty CTA coverage

Added opt-in `STRATA_MMQ_TILE_PROFILE=1` host counters for existing grouped local GU/down calls.
The diagnostic replays the exact pinned upstream J selector using the already-constructed `mmq_args.ncols_opt`, including current guarded J48 policy. It does not change dispatch or device arithmetic, add device copies or synchronize streams.
It reports rectangular/live/empty CTA counts, grouped by device/type/projection shape and selected I/J/K. Stream-K and unsupported count provenance are excluded.
"Live" includes terminal partially filled tiles; empty CTA share is not saved GEMM FLOPs. Upstream already skips empty CTAs before the product, after shared-ID initialization and a barrier.
Counters add CPU work and locking; profile-on timing is not promotion evidence. Measure profile-off controls and candidates separately.
No scheduler optimization is enabled or promoted yet.

### Diagnostic lifecycle correction

The first profile-enabled 8K run completed with valid phase timing but no CTA report.
Investigation found that serve-mode clean QUIT intentionally calls `std::_Exit(0)`; a C++ static destructor is therefore not a reporting hook even when process exit status is zero.
This was a diagnostic implementation error, not evidence of zero MMQ work.
The counters now emit an explicit locked cumulative snapshot after successful prefill pipeline drain, with a monotonic sequence number. Consume the final snapshot (or differences), never sum cumulative snapshots.
The collector is explicitly restricted to the observed Q2_0 grouped-local path; direct/other paths and stream-K are excluded.
The original incomplete run remains in private evidence. No performance qualification or main promotion used it.

Profile-off 2K/128 retained exactly the baseline token hash, MTP acceptance 59/65 and expert admission. Its PP 301.30 / TG 73.06 / wall 8.562 s remain baseline noise, not a gain.
In the first 8K diagnostic, the combine phase was only 0.5–0.7% of each reported stage timeline, and even that includes waits. This bounds the motivation for combine/HC work; the entire phase cannot be credited as removable time.

### Measured scope and compact scheduler prototype

The corrected 8K diagnostic emitted one complete snapshot: 27,399,000 rectangular CTAs versus 6,354,840 live CTAs, or 76.806% empty. Per device the empty fractions were 73.219% and 80.104%. Almost all covered calls selected J48/I64/K256. These are scheduling counts, not compute or time savings.

The prototype is deliberately narrow: gfx906, native Q2_0, 16 full-local-routing experts, the existing selected J48/I64/K256 configuration, no stream-K, current 4K chunk bounds. A 17-entry by-value prefix maps live tiles to expert/tile indices; upstream tile arithmetic is reused unchanged. It also omits the now-redundant shared-ID initialization/barrier before loading actual IDs. The copied outer-wrapper material retains the upstream MIT notice.
Build option `STRATA_GFX906_COMPACT_MMQ` defaults OFF; runtime `STRATA_GFX906_COMPACT_MMQ=1` is also required by the engine. The build pins the upstream scheduler SHA256 and checks device configuration at compile/run time. Unknown paths fall back.

Isolated qualification completed on both GPUs:
- 20 cases: GU/down × balanced/skewed/long-skew/zero-count/tail distributions × two devices.
- Shuffled destination IDs, nonzero absolute GU bounds, full output bytes and untouched canaries matched exactly.
- Each compact arm asserted that the candidate actually ran; a silent fallback cannot pass.
- Forty measured alternating AB/BA pairs per case after five warmups; paired medians and quartiles are in [compact-micro.json](compact-micro.json). Raw paired samples are retained privately.
- Skewed GPU-kernel gains were only about 0.5–1.4%. Balanced down and zero-row synthetic down cases were about 0.2–0.4% slower. This is not a universal win and not promotion evidence.

First same-binary cold 8K/128 screen:
- OFF: PP 490.20 tok/s, request wall 18.600 s.
- ON: PP 492.98 tok/s, request wall 18.505 s.
- All output token IDs, work, MTP acceptance 54/67 and 20,564 streamed experts matched.
- About +0.57% PP / -0.51% wall is below a trustworthy one-pair claim. Reverse-order confirmation is pending. No main promotion or deployment.

### Reverse order: performance claim rejected

The reverse ON→OFF fresh-process pair did not reproduce the first pair:

| Order | Mode | PP tok/s | Request wall s |
|---|---|---:|---:|
| First pair | OFF | 490.20 | 18.600 |
| First pair | ON | 492.98 | 18.505 |
| Reverse pair | ON | 392.69 | 22.751 |
| Reverse pair | OFF | 419.76 | 21.406 |

The reverse pair was -6.45% PP / +6.28% wall for ON. All four runs kept identical token IDs, requested work, MTP 54/67, expert admission, 20,564 streamed experts and the same candidate binary. HC exact/N4 dispatch counts also matched.
The first +0.57% therefore does not establish a reproducible end-to-end gain. **Main promotion is blocked.** No full 64K qualification is justified by these mixed results.

A comparison of the earlier diagnostic phase logs found nearly unchanged MMQ GU/down times but large first-chunk HC/generic-GDN phase differences; those phases include host/library/wait gaps. Their cause is not established. Do not blame the scheduler, clocking, or any single component from these observations alone.
A separate bounded diagnostic will repeat uncached requests within one persistent process, asserting read=8,192/reused=0 each time and recording phase/clock/load telemetry. This separates process-cold behavior from context-cold behavior; it does not replace or erase the fresh-process failures.
