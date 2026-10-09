# Strata gfx906: omit provably empty PCIe expert dispatch

Status: 2026-10-09. Qualified fork-stack prototype; default off. The 64K ABBA performance gate and request-time route transition check passed. 4K/200K qualification and API checks also passed. The immutable release is preserved; production was not promoted. This is a receipt and incremental-patch archive on `bench/gfx906-qualified-results`, not an implementation branch. Runtime source is unchanged; no upstream PR for this change has been created.

## Result

Four matched runs in A1–B1–B2–A2 order, each with 65,536 prompt tokens and 1,024 generated tokens, measured **+1.705616% token-generation throughput (TG)** with the optimization enabled. The two matched pair gains were **+1.643954%** and **+1.767305%**. Prompt-processing throughput (PP) changed **−0.016568%**. All 1,024 output IDs were identical across all four runs; acceptance and cache counters also matched.

This passes the bounded engineering screen: mean TG gain at least 1%, both pairs positive, and exact token IDs. Two pairs do **not** establish statistical confidence or general performance across workloads. Keep the feature opt-in; the completed qualification supports this bounded fork-stack result without establishing broader statistical confidence.

| Arm | Feature | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
|---|---|---:|---:|---:|---:|
| A1 | off | 104849.6 | 20168.6 | 625.047687 | 50.771992 |
| B1 | on | 104912.0 | 19842.4 | 624.675919 | 51.606660 |
| B2 | on | 104802.8 | 19826.8 | 625.326804 | 51.647265 |
| A2 | off | 104830.4 | 20177.2 | 625.162167 | 50.750352 |

TG gain is the ratio of mean B throughput to mean A throughput, minus one. PP uses the same method. PP is reported full prompt count divided by native prompt time; the last prompt token executes in the first decode window. TG is actual generated count divided by native decode time. Neither metric includes model load time; request wall time is recorded separately. The +1.71% figure is a decode-throughput result, not an end-to-end request speedup.

Configuration retained the qualified private gfx906 stack, 27/21 layer split, fixed expert placement, mode16 and fused grouped SwiGLU, int8 KV, effective PCIe share zero, context capacity 204,800, 19,078 total expert slots (9,900 primary), speculative setting 6, MTP maximum 4, lookup setting 3, and 15 pool workers. All arms used temperature 0, top-p 1, top-k 1 and seed 12345. Profiling and route tracing were disabled for performance measurement. Each arm recorded 648 accepted / 872 offered speculative tokens and 582,049 hits / 600,000 lookups, with no prompt reuse.

## Separate full-stack comparison against stable

A later **direct, fresh-process A1–B1–B2–A2 comparison** measured the combined selected winners against the existing stable control, with 65,536 prompt tokens and 1,024 outputs in every arm. The stable control already includes earlier campaign optimizations; it is **not stock upstream**. The combined binary is SHA-256 `050dd8dcbe7d3e9cfaeae870d45df872a1aecded6fff1e1d4611d52f1194c4f4`.

| Metric | Stable mean | Combined mean | Change |
|---|---:|---:|---:|
| PP tokens/s | 598.293877 | 624.848047 | +4.438316% |
| TG tokens/s | 50.524613 | 51.633338 | +2.194426% |
| Request wall latency | 129.831190 s | 124.736941 s | −3.923748% |

All 1,024 output IDs match across all four arms, independently rechecked from the receipt. The service restoration check passed. The run finished at 2026-10-09 06:24:42 UTC. These gains were measured directly, not obtained by adding isolated optimization percentages. They characterize the **combined stack**, and must not be attributed entirely to empty-PCIe dispatch elision. The isolated patch result remains **+1.705616% TG** from the earlier matched flag-off/flag-on screen. Two matched pairs in either screen do not establish statistical confidence.

## Change and correctness contract

The patch conditionally omits only the PCIe `native_expert_grouped` call in ordinary serial verification. It makes **no arithmetic change**. waitA, waitB and its fences, CPU doorbell/publication, waitCPU, all plan and result copies, VRAM expert calls, and combine remain unchanged.

The omission is permitted only when the stage's effective rounded integer PCIe numerator is zero and the actual grouped route is proven to perform no writes for zero groups. A zero numerator forces zero fetch quota and publishes zero PCIe groups. On the audited route, GU/down kernels return before reads or writes for zero groups, and fused SwiGLU has an empty half-open range. This proof does not apply indiscriminately to other grouped implementations, some of which can write scratch even for zero groups.

The conservative route guard requires gfx906, mode16, phase0, grouped-v1 off, fused SwiGLU on, V2/V2K off, H=2560, FF=640, GU type in {18,21,22,23,42}, and down type in {20,42}. The launcher and guard share the same cached route parsers. Unknown/nonzero numerator, unsupported layouts or routes, batch and pipeline paths, non-native paths, and all-resident verifiers including fallback retain the original call. Route settings and layouts must remain fixed for captured-graph lifetime.

Each verifier receives its own resolved stage numerator before prompt graph capture. The default unknown value is −1. A separate graph array caches the no-PCIe variant by window size T; capture and launch share one selector. Zero→positive→zero requests therefore select no-PCIe→full→cached no-PCIe, without destructive invalidation, new synchronization, or per-window allocation. Additional graph handles are destroyed after the existing stream synchronization. Capturing both variants can increase graph-executable memory; the current evidence does not quantify that increment.

## Evidence before the performance screen

### Readiness diagnostic

An 88-window diagnostic found all 4,224 layer samples empty and zero invalid samples. The CPU completion predicate was already satisfied for 3,950 samples. Raw empty-dispatch time was 1.136011 ms/window. Deducting ready waitCPU/marker control intervals and the whole probe cost produced a conservative engineering score of **0.695344 ms/window**, above the **0.589 ms/window** prototype gate.

This score justified one bounded prototype. It is not a rigorous lower bound or measured unprofiled speedup: marker kernels, readiness sampling and readback can perturb overlap and scheduling. waitB time was not credited because waitB is retained.

### Source and host checks

Independent source review found no correctness blocker in the guarded design. Arithmetic kernel source and existing wait/copy/combine sequences were unchanged. Source-derived host checks covered 384 route combinations, 7,744 layout/type combinations, 98 cached-parser cases, T1–8 graph transitions, unknown/nonzero values, mixed-stage shares, rounding boundaries, and rejected execution paths. These checks are host/source evidence, not a claim that every case was exercised on a GPU.

### Runtime route/cache transition

The same-process requested-share sequence **0→1.0→0** passed against matching flag-off requests. All three 32-token responses matched their corresponding control exactly. Six stage/T combinations were checked: T={1,2,4} across layers [0,27) and [27,48). The trace verified the specialized/full/cached-specialized transition, and the control performed no elision.

Actual PCIe groups per layer-window were **0.0→0.5→0.0**, confirming that the positive request restored real PCIe work rather than merely selecting a full graph whose group count happened to remain zero. The 0.5 value is an aggregate average, not a fractional individual group. Corresponding-share parity is the requirement; zero-share and positive-share outputs need not equal each other.

## Completed qualification and service restoration

- **4K:** one candidate-first/control pair, 4,096 prompt tokens and 1,024 outputs per arm. All output IDs matched exactly. Candidate PP/TG were 369.588364/56.983545 tokens/s versus control 369.605039/56.178542, giving **+1.432936% TG** and **−0.004512% PP**. Both arms recorded 684 accepted / 855 offered tokens and fixed 19,078 expert slots. This single pair corroborates the bounded result; it is not an independent statistical-confidence claim.
- **200K:** 200,000 prompt tokens and 256 generated outputs completed with exact parity reported against the existing reference. Candidate PP/TG were 597.693620/44.557385 tokens/s. Capacity was 204,800, resident KV 32,768, expert slots 19,078 total / 9,900 primary, and reported free VRAM 504 MiB. There was **no fresh 200K performance comparison**, so no 200K speedup is claimed. The sanitized aggregate includes both candidate IDs and the archived 256-ID reference with provenance. All 256 IDs were independently compared and match exactly.
- **API:** the temporary candidate passed tools, vision and parking checks. Its running process binary SHA-256 and expected flag whitelist were verified. Original compose/configuration files were restored byte-for-byte, and the stable API was healthy afterward.

The immutable release `gfx906-qualified-20261009` was preserved. **Production was not promoted.** Qualification finished at 00:30:44 UTC and API validation at 00:35:58 UTC on 2026-10-09. These results supersede all earlier pending or provisional qualification statuses.

## Compatibility and adoption limits

The patch applies mechanically to upstream `fb58e0dbc8399662c0e47c76578c6e878b14f6cf`, but that revision lacks the private mode16 route used in the proof and measurements. Accepting the integer environment value 16 upstream selects different fallback kernels; it does not recreate the qualified route. This patch is therefore **not standalone upstream-ready**.

The verified public fork snapshot `cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3` (tree `ffef85c8f48094c4d97bdba279e77069d34b2e60`) has exactly matching Git blob IDs for all five affected files versus the private prototype parent. This verifies the five affected parent blobs only, not identity of the entire public tree with the measured qualified stack. The incremental patch can be examined against those files; it does not by itself reproduce the measured stack. This does not establish standalone upstream compatibility.

Keep it as a qualified fork-stack patch or explicitly dependent follow-up. Supporting upstream-native modes needs a separate no-write contract and validation; do not broaden the guard to modes7/8 based on this evidence. No upstream performance, other-device, other-KV, model-quality, batching, or pipeline benefit is claimed. Exact token parity on the tested requests does not prove universal parity.

Enable with `STRATA_VERIFY_SKIP_EMPTY_PCIE=1`; unset or `=0` leaves it off. `STRATA_EMPTY_PCIE_TRACE` is a route-test aid enabled by presence, even if its value is 0. Keep that trace and diagnostic profiling flags unset for performance arms. Reject adoption if exact parity fails, a positive effective numerator selects an elided graph, ordering changes, or required qualification fails.

## Reproducibility artifacts

- Prototype base: `f152172332693c933b8a3104ce193d8a4315c2b4`, applied to the full qualified stack, not the bare base as a replacement.
- Verified public fork publication base: `cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3`; all five affected file blobs match the prototype parent. This archive does not modify runtime source or publish an implementation branch; no upstream PR for this change has been created.
- Archived patch: `bench/patches/2026-10-09-gfx906/archive-empty-pcie.patch`; five files, 87 additions / 7 deletions.
- Patch SHA-256: `7e41dbdb97df1f451ee7c3b5c70c248995d37c36db9650ab2b49a240004b2174`.
- Tested binary SHA-256: `050dd8dcbe7d3e9cfaeae870d45df872a1aecded6fff1e1d4611d52f1194c4f4`.
- Performance receipt: `empty-pcie-model-20261009.json` (finished 2026-10-09 00:21:04 UTC).
- Route receipt: `empty-pcie-route-validation-20261009.json`.
- Diagnostic receipt: `pcie-readiness-20261008-score.json`.
- Qualification receipt: `empty-pcie-qualification-20261009.json`.
- API receipt: `empty-pcie-api-20261009.json`.
- Separate full-stack receipt: `combined-vs-stable-20261009.json` (finished 2026-10-09 06:24:42 UTC).
- Sanitized aggregate: `empty-pcie-results.json`, with `model`, `qualification`, `route`, `api` and the separately labeled `combined_vs_stable` sections. It preserves all original model/qualification/combined-comparison output-ID arrays, numeric timings and decision values, plus the archived 200K reference IDs and provenance for independent parity checking. API fields are explicitly whitelisted; raw configuration, environment mappings, personal paths and secrets are excluded.

The accompanying archive preserves the measured receipts and incremental patch; it does not promote the runtime or claim an upstream implementation merge.

## Receipt recheck

Run `python3 bench/check_gfx906_empty_pcie_results.py bench/results/2026-10-09-gfx906-empty-pcie/empty-pcie-results.json --selftest`. This recomputes timing arithmetic and the ABBA gate, checks every preserved output ID including the archived 200K reference, and validates recorded route/API coverage. It passed, including six deliberately corrupted receipts that were rejected. This is receipt validation, not a rerun of GPU/API tests.

The measured system used two 16-GiB gfx906 wave64 devices (runtime name AMD Radeon Pro VII), stock-high mode with 190 W caps. Pinned container image: `sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646`; pinned llama.cpp: `3cf03257f219afbe7334045ff7c6a06ac68c627d`. The compiled stack includes previously qualified HC/J32, PR1525 dequantization and guarded QSA swizzle. Its HC path is workload-qualified; this report does not claim universal BF16/FP16 GEMM equivalence.
