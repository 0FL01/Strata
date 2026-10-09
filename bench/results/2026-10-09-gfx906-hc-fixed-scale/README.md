# HC fixed-scale specialization: parked after a synthetic component screen

Date: 2026-10-09 UTC. Decision: **PARK_WITHOUT_MODEL_QUALIFICATION**.

The two isolated gfx906 fixed-scale converters remove the generic division sequence and reduce VGPR use from 7 to 5. Exact GPU parity passed for all 65,536 BF16 encodings at both scales, including NaNs and signed zeros. The largest predeclared whole-scenario optimistic weighted saving was **2.5656605928 ms**, below the **1,003.739604 ms** screening gate. This is an engineering screen using synthetic stress distributions and source-derived maximum call counts, not a measured model gain or a whole-model bound.

No candidate model build, model run, promotion or deployment was performed. The existing c183 control remains [646.4538059 PP / 53.8075120 TG tokens/s at 64K/1,024](../2026-10-09-gfx906-c183-profile/README.md). Those are baseline measurements, not results of this candidate. This prefill-only candidate does not establish a TG improvement or remove the bundled decode HC0/HC1 intervals.

## Mechanism and source binding

The actual frozen c183 scaled exact-input converter uses runtime scales 4096 for weights and 512 for activations. Its exact 428-byte device function was bound to the source, host object, archive and executable. The original generic division sequence occupies 11 instructions / 72 bytes. The compiler already elects one active lane per wave for each of three Boolean guard atomic operations; manual atomic aggregation was therefore not pursued.

The isolated candidate supplies two kernels with constexpr scales. It retains the multiplication, FP16 conversion, roundtrip division expression, bit comparison and three atomic predicates; no approximate reciprocal or fast-math change was proposed. The baseline ABI has five explicit arguments, including scale; the candidates have four. Production source and executable were unchanged. Existing alpha, stats reset/copy, synchronization, diagnostic and fallback behavior would remain required for any later integration.

## CPU and static resource evidence

The CPU IEEE-model proof enumerated all 65,536 BF16 encodings per scale. It established the modeled arithmetic/guard equivalence for 65,282 non-NaN patterns, but explicitly did not prove the 254 NaN patterns per scale or actual GPU conversion semantics. It also checked all 63,488 finite half payloads and both infinities per scale. GPU parity was still required because signed-zero and NaN behavior can depend on compiled FP16 mixed-FMA lowering.

Both candidate kernels passed the independent raw-ELF metadata and opcode audit: 5 VGPR, 20 SGPR, wave64, zero LDS, scratch or spills, no dynamic stack, no generic division sequence, and retained elected-active-lane atomics. The baseline is 7 VGPR / 20 SGPR with the same zero-resource conditions. The audit checked 219 candidate opcode words covering all 876 text bytes and 107 baseline words. Static instruction/resource reductions are not evidence of faster model execution.

## Historical tiny sanity failure and strict recovery

The original tiny sanity native process exited zero, but its wrapper **failed with JSONDecodeError** because three function-name log records contained unescaped quotes. Its cleanup passed. This original wrapper result remains failed.

A separate controller-only recovery accepted only those three exact, hash-pinned malformed lines and independently checked the preserved raw evidence: 14 pairs / 28 launches, exact half outputs, all 16 stats words, guards and 404 zero HIP return codes. For BF16 negative zero, both baseline and candidate produce half positive zero and set the exactness-failure flag at both scales. This is parity with baseline behavior, not preservation of the signed zero. Original files were not modified and no GPU rerun was used. CPU serialization tests covered the corrected future logger. Recovery validates the existing tiny native evidence; it does not turn the original wrapper into a PASS.

## Exhaustive raw GPU equivalence

The subsequent exhaustive run and independent controller audit both passed. Every BF16 encoding was exercised once per scale in an n=1 baseline/candidate pair with a separate zeroed stats block, avoiding the masking inherent in an aggregate OR-only comparison. There were 131,072 scalar pairs and 36 mixed boundary/tail/offset pairs: **131,108 pairs / 262,216 launches** across 548 batches.

Every half output and all 16 stats words matched, canaries were intact, inactive stats remained zero, n=0 wrote nothing, and all four stages were consistent. Both native and wrapper exits were zero; cleanup passed. The independent auditor verified the full raw results and build manifests and reran the offline rechecker without GPU use. This establishes equivalence to the exact bound baseline for the tested scales and cases, not model integration.

## One-shot timing recipe and decision

The screen used the two previously built, hash-pinned ELFs on GPU0. Only its host controller was built. Five descriptors were tested: W n=3,276,800 at scale4096 (maximum 1,728 calls), and X n=41,943,040; 41,932,800; 1,310,720; 1,310,400 at scale512 (maximum 810; 54; 810; 54 calls). These are maxima, not measured converter frequencies; 1,728 attempts and 531 taken paths do not establish launch counts.

Three predeclared synthetic distributions were accepted values, sparse rejects and dense rejects. Two regimes were warm and scrub-conditioned with a separate 64-MiB footprint. Scrub-conditioned does not guarantee cold caches. Thirty cells each contained three ABBA quartets, for 360 measured launches. Together with 32 full-correctness preflight launches, 180 same-arm warm predecessors and 180 common-baseline scrub predecessors, the fixed total was **752 launches**. No rerun-to-win, adaptive sampling or extra timing warmup was allowed.

Each quartet delta is the mean of its two baseline samples minus the mean of its two candidate samples; each cell uses the median of its three quartet deltas. Within each complete pattern/regime scenario, five deltas are weighted by the maximum call counts. Signed sums are retained; the optimistic estimator clips negative descriptor deltas to zero before weighting. The largest optimistic sum among the six whole scenarios is compared to the gate. Best cells from different scenarios are never combined.

The terminal run completed at 21:20:05 UTC with native and wrapper exits zero and cleanup PASS. Its largest optimistic weighted estimate was 2.5656605928 ms, versus the 1,003.739604 ms needed for a +1% PP throughput improvement at unchanged baseline work. The predeclared rule therefore parks this candidate without model qualification. Event brackets measure device-stream elapsed time for a single launch and may contain submission gaps; these small differences do not establish a general latency effect, statistical significance or repeatability. Maximum counts, synthetic inputs, cache state, overlap and scheduling prevent interpreting the weighted estimate as an actual model saving or bound.

## Audit and publication scope

Independent timing audit: **PASS_SCREEN_RAW_PARITY_TIMING_AND_GATE_AUDIT**. The auditor checked all 2,288,792,064 preflight bytes, exact inputs/outputs/stats/canaries, 752 launches, all 360 event-bit/sample matches and 4,525 zero HIP return codes. Full result/build manifests and cleanup passed. An offline analysis rerun was byte-identical, and all six scenario sums and the PARK decision were independently recomputed. No GPU rerun was performed.

[Machine-readable metrics](metrics.json) retain sanitized numbers and provenance hashes. Full private raw receipts, binaries, logs and any capture/model payloads are excluded from this report-only archive update. No production code, engine settings, credentials or existing implementation PR is changed.
