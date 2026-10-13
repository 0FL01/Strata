# gfx906 qualified receipts and incremental patch archive

This branch, `bench/gfx906-qualified-results`, is an evidence archive, **not an implementation branch**. Its commit adds only files under `bench/`. Runtime source remains identical to public parent `cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3` (tree `ffef85c8f48094c4d97bdba279e77069d34b2e60`). No production promotion or upstream PR is made by this archive.

## What the measurements establish

- [Empty-PCIe report](results/2026-10-09-gfx906-empty-pcie/empty-pcie-report.md): isolated flag-off/on TG +1.705616%, two matched ABBA pairs, exact 1,024-token parity.
- [Primary-commit report](results/2026-10-09-gfx906-primary-commit/primary-commit-report.md): incremental TG +1.212502% on the already-qualified empty-PCIe stack, two matched ABBA pairs, exact 1,024-token parity.
- The separate pre-primary-overlap full-stack comparison versus the user's stable control measured PP +4.438316%, TG +2.194426%, request latency −3.923748%. This is not stock-upstream performance and is not the sum of isolated patch gains. There is no fresh post-overlap full-stack comparison here.
- 4K checks are single pairs. 200K checks establish capacity and archived-reference exact parity, with no fresh performance control. Two ABBA pairs do not establish statistical confidence or general parity.

## Dependency and reproduction limits

The measured full stack includes qualified **HC/J32, PR1525 dequantization and guarded QSA swizzle**, in addition to the two incremental patches archived here. **Applying only these two patches does not reproduce the headline full-stack measurements.** The archive does not contain a complete independently buildable snapshot of the qualified runtime.

Prototype provenance names `f152172332693c933b8a3104ce193d8a4315c2b4` plus qualified fork-stack changes; that bare commit is not the complete measured stack. Primary commit overlap is based on that qualified stack **after** the empty-PCIe patch. The five affected parent file blobs were verified identical to the public `cfc7eeef` snapshot. This is file-level identity only, not proof that the entire public and prototype trees match. Mechanical application and host-only tests below do not establish runtime equivalence or upstream readiness.

Patch order and SHA-256:

1. `patches/2026-10-09-gfx906/archive-empty-pcie.patch`: `7e41dbdb97df1f451ee7c3b5c70c248995d37c36db9650ab2b49a240004b2174`
2. `patches/2026-10-09-gfx906/archive-primary-commit.patch`: `3c87611bd665e3cd4a3525d1536977e2c7a7b8ce22730fc8fa4c8ea36f532d90`

The primary patch is the corrected dual-backend-macro version. Empty-PCIe is enabled with `STRATA_VERIFY_SKIP_EMPTY_PCIE=1`. Primary overlap is enabled by presence of `STRATA_PRIMARY_COMMIT_OVERLAP`; a value of `0` still enables it. Presence of `STRATA_COMMIT_SYNC` forces baseline. Leave diagnostic tracing unset for performance measurements.

## Offline receipt validation

From this branch's checkout root, with Python 3:

```sh
python3 bench/check_gfx906_empty_pcie_results.py bench/results/2026-10-09-gfx906-empty-pcie/empty-pcie-results.json --selftest
python3 bench/check_gfx906_primary_commit_results.py bench/results/2026-10-09-gfx906-primary-commit/primary-commit-results.json --selftest
```

Both passed during archive preparation, including six rejected corrupted receipts each. The empty-PCIe validator checks the isolated experiment, qualification and route/API fields; it does not independently validate the separate `combined_vs_stable` section. All original output-ID arrays are preserved in the JSON. API summaries use an explicit whitelist. Source receipt names are provenance labels, not promises that every original raw file is separately present. Recorded publication/restoration fields describe the original receipt-time state.

## Host eligibility test without modifying the archive checkout

Requires Git, Python 3 and a C++17 compiler. Run from the archive checkout root. This applies patches only to a new temporary detached worktree, runs the extracted actual eligibility block with mocked device calls, then removes that temporary worktree. It does not compile the engine or access a GPU.

```sh
archive_root="$PWD"
tmp="$(mktemp -d)"
git worktree add --detach "$tmp/source" cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3
(
  cd "$tmp/source" &&
  git apply --unidiff-zero "$archive_root/bench/patches/2026-10-09-gfx906/archive-empty-pcie.patch" &&
  git apply "$archive_root/bench/patches/2026-10-09-gfx906/archive-primary-commit.patch" &&
  python3 "$archive_root/bench/test_primary_commit_guard.py" "$tmp/source"
)
status=$?
git worktree remove --force "$tmp/source"
rmdir "$tmp"
exit "$status"
```

The same patch sequence was checked on the five verified public-parent blobs plus the public `gfx_arch.hpp` header during archive preparation: 63 compiled mocked cases passed, 21 each for gfx906 compatibility, native HIP and unsupported-backend definitions. A full fresh worktree was not materialized during this preparation. This is host/source evidence, not GPU fault injection, runtime qualification or a new performance run.


## QSA reduce12: qualified frozen-stack increment (2026-10-09)

[Final report](results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-report.md) · [full receipt/token IDs](results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-results.json).

Native 64K + 1,024 outputs: candidate PP **646.536120 tokens/s**, TG **53.106939 tokens/s**; incremental **+3.440197% PP / +1.581280% TG** versus the retained qualified HC/J32/dequant/QSA/empty-PCIe/primary-overlap stack. Both matched ABBA pairs are positive and all 1,024 IDs match. 4K, 200K capacity/archived parity, and API checks passed; 4K is a single pair and 200K has no fresh performance comparison. This is not a new combined-versus-stable measurement. The separate micro result is component latency reduction, not model throughput gain.

Release `gfx906-qualified-20261009-reduce12`, binary SHA256 `ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9`, is **not promoted**; live API remains stablece. Both frozen-base and public-1f555 patch artifacts are linked in the report. Public-source port is only source-reviewed/apply-checked, with no separate full upstream build or runtime qualification claimed. The archive still changes only `bench/`, not runtime sources or PR1661. Earlier two-patch reproduction limits above continue to describe the earlier archived experiments; the new patch alone likewise does not recreate its full qualified stack.

From this archive checkout root:

```sh
python3 bench/check_gfx906_reduce12_results.py bench/results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-results.json --selftest
```

The offline validator passed and rejected all 15 corruption cases. This verifies receipt consistency, not a new hardware run. Raw token-ID arrays and the historical micro report/receipt are preserved. [Future public-source probe instructions](results/2026-10-09-gfx906-qsa-reduce12/PROBE-REUSE.md) are not executed results.


## New direct combined and public-component evidence

[Numeric report](results/2026-10-09-gfx906-direct-ff34-vs-ce/README.md): direct whole-combined-versus-optimized-stable 64K/1,024 ABBA gives **+8.101919% PP / +5.049872% TG**, with all four complete token-ID arrays equal. This supersedes the historical absence of a fresh post-overlap combined comparison above. It is not stock-upstream performance or isolated reduce12 attribution. The new public derivative omits private filesystem and service-configuration provenance; its exact validation limits are stated in the report.

[Public reduce12 component receipt](results/2026-10-09-gfx906-qsa-reduce12/public-component-numeric.json) separately records both-GPU full-output parity, ISA and **26.728519% / 26.510032% component latency reduction** for the exact public QSA translation unit with a frozen support archive. This advances the earlier source-only public-port status, but is not a full public-tree build or public-port model qualification.

The separate [implementation commit](https://github.com/0FL01/Strata/commit/08a844d3f31199798b7ea78dc5c8512fd9c17e79) stacks on #1661; the incremental diff is one source file +74/−3. [Prepared upstream PR body](results/2026-10-09-gfx906-qsa-reduce12/PR-DRAFT.md) is available for manual submission after the connector returned HTTP403, `Resource not accessible by integration`. #1661 was unchanged. The archive itself still only changes bench artifacts.


## Scalar FIT17: frozen combined-stack model studies

[Report](results/2026-10-09-gfx906-qsa-fit17/README.md) and [numeric receipts](results/2026-10-09-gfx906-qsa-fit17/qsa-topk-fit17-benchmark-results.json): two separate 64K/1,024-output ABBA studies on the same frozen c183 binary. Suffix-disabled fixed policy gives **+1.413177% TG / −0.001826% PP** with matched counters; ordinary adaptive policy gives **+1.299911% TG / +0.084680% PP** with exact IDs but documented second-pair counter drift. Do not pool these different workloads or attribute the adaptive result to constant work.

All eight full model-output arrays match historical IDs. Separate 4K/200K candidate checks have exact reference IDs and establish correctness only; fallback ownership is explicitly source-inferred, not instrumented. The original component gate failure, historical-counter gate failure and parser infrastructure failure remain preserved. This evidence binds the private combined c183 stack; no public-port build/GPU result or stock-upstream gain is claimed here. No implementation branch or existing PR body is changed by this archive update.

Run from this checkout root (or run the report's relative command after entering its directory):

```sh
python3 bench/results/2026-10-09-gfx906-qsa-fit17/check_qsa_topk_fit17_benchmark_results.py bench/results/2026-10-09-gfx906-qsa-fit17/qsa-topk-fit17-benchmark-results.json --selftest
```

Offline consistency validation passed, including 18 rejected corruption cases. Full numeric IDs, source hashes and failure evidence are retained; private host paths, configuration contents and raw logs are excluded.


### FIT17 public selector component follow-up

[Separate public component report](results/2026-10-09-gfx906-qsa-fit17/PUBLIC-COMPONENT.md): 54 processes completed on both gfx906 devices, with 46 correctness and 8 ABBA timing processes. Direct public selector TU/headers, no support archive. Captured-layer selector latency reduction is **25.7331752864% / 26.0592091451%**; the original 30% discovery gate remains failed. Exact public/private selector ISA comparison and scratch/spill caveats are documented. This advances component qualification only, not a full public-tree build or public-port model result. Existing numerical model receipts remain unchanged.


## Complete c183 stack versus optimized stable ce

[Direct benchmark report](results/2026-10-09-gfx906-direct-c183-vs-ce/README.md): fresh-process 64K/1,024-output A1/B1/B2/A2 gives **+8.147793% PP / +6.509285% TG** against already optimized stable ce. Both pairs are positive; all complete IDs, topology and available aggregate counters match. Unavailable optional counters stay null. Timing-trained adaptive policy means observed counter equality is not proof of constant work. This is a direct whole-stack comparison, separate from ff34-versus-ce; no gains were summed and no stock-upstream or isolated-selector attribution is made. The receipt validator passed 14 corruption tests. Earlier artifacts remain unchanged.


## WIDE51: parked isolated real-200K selector experiment

[Report](results/2026-10-09-gfx906-wide51/README.md) and [numeric metrics](results/2026-10-09-gfx906-wide51/metrics.json): one fresh-process ABBA per physical gfx906 GPU measured **1.654291% / 0.588942% lower isolated selector latency** on the two actual 200K captures. All 12 correctness/timing processes passed parity and safety checks. WIDE51 is parked as an engineering prioritization decision; there was no predeclared speed threshold. One ABBA per device does not establish statistical significance or broad repeatability. No model-throughput or tokens-per-second gain is claimed; capture payloads remain private.


## Radix-stop: parked before GPU qualification

[Report](results/2026-10-09-gfx906-radix-stop/README.md) and [numeric metrics](results/2026-10-09-gfx906-radix-stop/metrics.json): original radix-stop and its single lower-live-state repair both compiled, then failed the unchanged scratch/spill resource gate (wrapper exit 14). All 13 old functions retained exact machine bytes, metadata and remarks. CPU exact-output proofs and all 16 captured-row replays passed for both; 13 modeled early stops are not a measured time fraction or speedup. No candidate GPU test, paired timing or model qualification ran. Both failures are preserved; the line is parked without promotion.


## Current c183: diagnostic profile refresh

[Report](results/2026-10-09-gfx906-c183-profile/README.md) and [numeric metrics](results/2026-10-09-gfx906-c183-profile/metrics.json): one fresh control/profile pair retained exact 1,024-ID parity. Control measured **646.453806 PP / 53.807512 TG tokens/s**. Profiling also disables the main shared fork, so observed phase-time increases and counter drift do not isolate profiler overhead or qualify an optimization. Timestamp ISA and both runtime clock rates were verified. PP views, GPU stages and nested CPU timers are non-additive; HC labels include bundled work. No optimization patch or promotion resulted.


## HC fixed-scale: parked after synthetic component screening

[Report](results/2026-10-09-gfx906-hc-fixed-scale/README.md) and [numeric metrics](results/2026-10-09-gfx906-hc-fixed-scale/metrics.json): fixed-scale specialization removes generic division and reduces VGPR 7 to 5, with exhaustive actual-GPU output/stats/guard equivalence at both scales. The original tiny wrapper serialization failure and separate strict raw recovery remain disclosed. A fixed 752-launch / 360-sample synthetic screen gives a largest within-scenario optimistic weighted saving of **2.5656605928 ms**, below the **1,003.739604 ms** gate; **PARK_WITHOUT_MODEL_QUALIFICATION**. Maximum call counts and synthetic stress distributions are not a measured model gain or bound. No candidate model build, promotion or TG improvement is claimed.


## HC guard observations: attribution and lifetime investigation only

[Report](results/2026-10-09-gfx906-hc-guard-observation/README.md) and [numeric metrics](results/2026-10-09-gfx906-hc-guard-observation/metrics.json): independent counts and cost audits reconcile 192 weights / 576 attempts, 203 taken / 373 exactness rejections, and 20 W-bad weights with 40 repeats. Most rejections are X-only (313). The conditional 64K host-wall screen is **13,579.974339 ms** against a **1,003.739604 ms** threshold, but includes required queued predecessor work and intentionally double-counts stage overlap. **ATTRIBUTION_AND_LIFETIME_INVESTIGATION_ONLY**: no removable-cost, model-bound or gain claim, no safe cache lifetime established, no cache patch or promotion. The exact c183 baseline remains unchanged.


## Primary-only HC W-negative cache: parked after model ABBA

[Report](results/2026-10-10-gfx906-primary-hc-negative-cache/README.md) and [numeric metrics](results/2026-10-10-gfx906-primary-hc-negative-cache/metrics.json): one fixed fresh-process 64K/1,024-output ABBA gives **+0.2101832693% PP / −0.0168454149% TG** versus the retained combined c183 R&D control. Exact historical IDs, all available counters, raw lifetime and cleanup checks passed; unavailable optional counters remain null. PP misses the predeclared 1% gate and TG misses the conservative zero-percent floor, without a significant-regression claim. **PARK**: no rerun, peer expansion, promotion or deployment. Qualification observed 324 primary candidates / 11 learned keys / 22 hits; 302 guards is inferred. Full 55-device-module equality and linked TLS audits passed. This does not prove constant work, isolated guard savings, general correctness or a public-tree build. Stable ce deployment is unchanged.


## QSA merge: parked baseline exposure screen

[Report](results/2026-10-10-gfx906-qsa-merge-exposure/README.md) and [numeric metrics](results/2026-10-10-gfx906-qsa-merge-exposure/metrics.json): unchanged c183 module35 synthetic replay gives primary GPU0 hot/rotate8 weighted exposure **821.6242314585002 / 819.9847139062499 ms**, below the **1003.739603960396 ms** screening threshold. Each device completed 34 cells, 476 samples, 4,624 launches and 272 preflights; source/ABI and actual raw audits passed. **PARK_WITHOUT_MODEL_QUALIFICATION**. Peer GPU1 is descriptive only; GPU events can include host dispatch gaps, masks are synthetic, and weighted extrema are not bounds. No candidate optimization, model PP/TG gain, rerun, promotion or deployment.


## Q2_0 K640 MMQ tail: parked after synthetic timing screen

[Report](results/2026-10-10-gfx906-mmq-q2-k640-tail/README.md) and [numeric metrics](results/2026-10-10-gfx906-mmq-q2-k640-tail/metrics.json): both-device full raw-bit synthetic replay and isolated component timing passed. Core median latency savings **10.993426–11.033575%** missed the separate frozen 12% campaign gate in both regimes/devices, despite full-grouped savings **12.118388–12.250872%**. K768 control slowed **0.226946–0.544809%**, within tolerance, not zero regression. **PARK_NO_MODEL_QUALIFICATION**. Original macro-OFF and compile-scope failures remain disclosed beside separate reproduction, static-admission and actual raw audits. No model gain, rerun, promotion or deployment.


## CPU pool spin: parked after a fixed 64K ABBA regression

[Report](results/2026-10-10-gfx906-cpu-pool-spin/README.md) and [numeric metrics](results/2026-10-10-gfx906-cpu-pool-spin/metrics.json): changing only the frozen c183 CPU pool spin setting from 20,000 to 100 us gives **+0.018434% PP / -2.085543% TG**, with both TG pairs negative. All five full 1,024-ID arrays and all clean-arm available counters/checked affinity matched; five optional counters remain unavailable. **PARK_POOL_SPIN_100US**. Separate baseline-only CPU observations do not establish useful work, candidate CPU savings or wakeup-latency causality. One ABBA is descriptive; no tuning, rerun, promotion or deployment.


## Dedicated Q2_0 K640 MMQ: four parked variants

[Report](results/2026-10-10-gfx906-mmq-q2-k640-dedicated/README.md) and [numeric metrics](results/2026-10-10-gfx906-mmq-q2-k640-dedicated/metrics.json): v1 parked before GPU at 104 allocated VGPRs. V2 reached 64 VGPRs/zero spills and exact semantics but regressed **26.195647–27.955291% in eligible component latency**. V3 restored original dot scheduling with literal stride ten, reached 80 VGPRs/zero spills and exact semantics, but core savings **3.594554–4.471563%** and 14/16 eligible cells missed the frozen component gate. V4 restored the shared loader at 80 VGPRs and passed the isolated timing gate, but core savings **11.308692–11.600070%** still missed the unchanged 12% campaign threshold. **PARK_NO_MODEL_QUALIFICATION**. Failed raw scope receipts remain alongside separate proven relocations. Separate runs are not paired cross-version comparisons; no register-only causality, model gain, promotion or deployment.


## Peer-prefill CPU1: counter-gate failure, no qualification

[Report](results/2026-10-10-gfx906-peer-prefill-cpu1/README.md) and [numeric metrics](results/2026-10-10-gfx906-peer-prefill-cpu1/metrics.json): baseline CPU0 role diagnosis led to a fixed C,A,B,B,A,C placement screen. All seven full 1,024-ID arrays and placement/restoration checks passed, but frozen-control C2 changed offered/lookups/hits/suffix work and the runner exited one. Descriptive PP differences **+2.086100% ON/OFF / +2.093669% ON/frozen** do not qualify the result; ON/OFF TG **-0.009673%** and its negative first pair independently fail the strict gate. **NO_QUALIFICATION**. Unpaired CPU/runqueue diagnostics are not causal speed or removable-wait estimates. No exclusion, rerun, promotion or deployment.


## Prefill existing-wait attribution: diagnostic only

[Report](results/2026-10-10-gfx906-prefill-sync-attribution/README.md) and [numeric metrics](results/2026-10-10-gfx906-prefill-sync-attribution/metrics.json): one independently audited diagnostic attributes **17.574090553 CPU-s / 10.336731%** of **170.015937957 stage-thread CPU-s** to six existing wait sites. The **152.441847404 CPU-s residual is unclassified**, not useful compute, launch or GPU time. All 1,024 IDs/work and 17 scopes/130 buckets passed. Main wall 94.475046155 s excludes the final peer tail; full span is 99.740547885 s. **DIAGNOSTIC_ONLY**: no speed, critical-path or performance qualification claim, and the rejected CPU1 screen remains unchanged.


## Prefill CPU samples: HSA wait/event leaves, incomplete callers

[Report](results/2026-10-10-gfx906-prefill-cpu-profile/README.md) and [numeric metrics](results/2026-10-10-gfx906-prefill-cpu-profile/metrics.json): 11,533 user-space CPU samples include 4,524/4,565 main-thread samples (**99.102%**) in HSA WaitRelaxed functions. All-thread wait/event leaf share is **98.500%**, with no recorded loss/throttling. These are sampled CPU-residency shares, not model wall-time or removable cost. All 6,968 nonmain callchains are empty; every stack reached the 4,096-byte capture cap. Caller attribution is incomplete and the interval can include initial decode. No speed qualification; retained capture/parser failures and privacy limits are documented.

## 2026-10-10: HIP blocking synchronization screen

[Report](results/2026-10-10-gfx906-hip-blocking-sync/README.md) · [Metrics](results/2026-10-10-gfx906-hip-blocking-sync/metrics.json). Technical execution and all seven arms' exact outputs/available work passed; performance qualification failed. Descriptive PP: +1.284241% ON/OFF and +1.327069% ON/frozen; companion TG: -0.006305% and -0.103285%. D0 CPU is full-request and lacks a matched OFF CPU trace. No promotion.

The [CPU profile](results/2026-10-10-gfx906-prefill-cpu-profile/README.md#follow-on-offline-unwind-check-append-only-caveat) also adds the same-capture selective offline check: 509 selected samples recovered frames, mostly leaf-only; caller attribution remains incomplete and no speed evidence was added.

## 2026-10-10: clean v0.1.42 release validation

[Report](results/2026-10-10-gfx906-v0142-release-validation/README.md) · [Metrics](results/2026-10-10-gfx906-v0142-release-validation/metrics.json). Pristine release 61b3fb5, same-binary combined query-swizzle/reduce12 OFF/ON: 4K/128 trace parity and cold 64K/1024 ABBA exact full IDs/available work; both fixed gates PASS. PP +4.593492%, TG +1.816550%, both pairs positive. Separate two-GPU component parity covers 26 full dumps and 36.186048%/36.131370% component latency reduction. Release-local validation only; no c183 speed comparison, individual-flag model attribution, service promotion or 200K qualification.

## 2026-10-10: release-local top-k REG2/FIT1 stack

[Report](results/2026-10-10-gfx906-v0142-topk-stack/README.md) · [Metrics](results/2026-10-10-gfx906-v0142-topk-stack/metrics.json). Technical build/ISA/component/full-model checks PASS; strict performance screen FAIL. TG +2.564108% with positive pairs, but first PP companion pair -0.053470% violates the frozen rule (PP mean +0.113856%). All diagnostic and clean full IDs/work/capacity matched. The 56 internally checked component processes and isolated FIT17 latency reductions of 26.035077%/26.291777% are separate evidence. No promotion, retry, per-PR attribution or cross-release gain claim.

## 2026-10-10: release-local primary-commit overlap

[Report](results/2026-10-10-gfx906-v0142-primary-commit/README.md) · [Metrics](results/2026-10-10-gfx906-v0142-primary-commit/metrics.json). Technical validation PASS across eight processes / twelve exact requests; scientific performance FAIL. TG +1.242043% with positive pairs, but first PP companion pair -0.186609% violates the unchanged rule (PP mean +0.293981%). QON recorded 39 queues / 44 drains, then zero queues / one drain on the second cold request. Raw ELF equality remains false; a separate strict CUID structural proof passed. No rerun, promotion, top-k treatment or cross-release gain claim.

## 2026-10-11: empty-PCIe observer V1 failure / V2 diagnostic

[Report](results/2026-10-11-gfx906-v0142-empty-pcie-observer/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-empty-pcie-observer/metrics.json). V1 host-macro failure preserved; corrected V2 fresh OFF/OBS/OFF passed exact 64K/256 outputs/work and diagnostic quality. Four sites × 93 windows yielded 372 zero-count records; local median group brackets 29.12 us versus adjacent-marker p95 3.04 us. Original pre-wait predicates were false in 4/6/5/0 windows and waits remain. Local source-proposal signal only; no optimization, removable-time estimate, 48-layer extrapolation or promotion.

## 2026-10-11: release-local empty-PCIe elision

[Report](results/2026-10-11-gfx906-v0142-empty-pcie-elision/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-empty-pcie-elision/metrics.json). Technical checks PASS across eight processes / twelve submitted requests (eleven complete plus expected refusal); scientific performance FAIL. TG mean +1.040069% with positive pairs, but first PP companion pair -0.107024% violates the unchanged rule (PP mean +0.709565%). Component CID failure and native V1 missing-owner trace failure remain preserved. Historical 1,480-record component evidence is explicitly rebound to an identical component binary, not rerun. No promotion, dropped pair, timing retry or cross-release gain claim.

## 2026-10-11: current-release PP and GDN conversion observations

[Report](results/2026-10-11-gfx906-v0142-gdn-conversion-profile/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-gdn-conversion-profile/metrics.json). Separate broad PP and conversion-only diagnostics retain frozen default7 semantics. Broad profiling matched all 1,024 IDs/work; conversion-only 64K/1 matched the first ID and reconciled 1,728 successful conversions across 17 owner/run records. Primary/peer conversion envelopes are 1,733.663593/1,301.892323 ms, never summed. A 1% reference PP throughput gain requires 1,036.092079 ms direct saving, about 59.76% of the primary envelope, not a predicted speedup or global bound. Submission-gap, overlap, memory and collection-failure limits remain explicit. No optimization patch, caching, promotion or performance qualification.


## 2026-10-11: strict HC component pass, hypothetical timing gate failure

[Report](results/2026-10-11-gfx906-v0142-strict-hc/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-strict-hc/metrics.json). Both-device synthetic full-output component checks passed all 64 cases (24 fast / 40 fallback). Corrected V2 GPU0 timing passed all 8 references and 128 warmup/measured sample checks, with all 12 fast quartets positive; the frozen hypothetical `528*S − 1200*P` screen nevertheless gives **−64.813104 ms**, below **+1036.092079 ms**. **PARK_INSUFFICIENT_HYPOTHETICAL_SIGNAL**; GPU1 timing was skipped by the fixed gate. V1 lifecycle failure remains invalid, and V2's repair branch was not used. A includes strict-enabled null-scratch rejection cost. Current-model activation is unknown; no all-workloads rejection, model gain, retry or promotion claim.


## 2026-10-11: historical c183 recovery and release inclusion audit

[Report](results/2026-10-11-gfx906-c183-recovery-inclusion/README.md) · [Metrics](results/2026-10-11-gfx906-c183-recovery-inclusion/metrics.json). One cold historical c183 observation reproduced every 1,024-output ID at **646.567331 PP / 53.748202 TG**, but the unchanged work gate failed: offered 872→874, hits 582049→582988, lookups 600000→600960 and suffix 5/9/16→6/11/20. This is descriptive near-54 TG recovery, not equal-work qualification or a new speedup. The historical integrated winner remains distinct from pristine v0.1.42: query/reduce and basic MMQ survive; strict HC, J32 override, primary overlap, empty-PCIe elision and REG2/FIT17 are absent. Exact historical compiled dequant identity is unresolved; current Q8 vectorization is present. Historical and release top-k gates/treatments differ; the release strict failure does not disprove the historical winner. No rebuild, retry or promotion.


## 2026-10-11: release tail-skip causality and adaptive-work correction

[Report](results/2026-10-11-gfx906-v0142-tail-causality/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-tail-causality/metrics.json). Reusing the existing release binary with only tail skipping set to 0 restored all 32 historical prefix IDs, then all 1,024 historical IDs. Retained default-release output differs at 999 positions, beginning at index 13. Actual-raw audits passed 71/69 checks; source/default and process bindings strongly support fixture-local tail-skip causality. Full-run **626.242241 PP / 47.779468 TG** is descriptive, with changed work and no equal-work qualification. Fresh c183 recovery work exactly recurs in historical FIT17 adaptive B2, so it is not a novel anomaly; its prior frozen-reference gate remains FAIL. Historical c183 near-53.75 TG and the release's unpruned baseline remain separate. Transfer timeout resumed the frozen archive only, with no GPU rerun. No general-quality guarantee, promotion or runtime source change.


## 2026-10-11: unpruned fixed-policy REG2/FIT17 screen

[Report](results/2026-10-11-gfx906-v0142-topk-fixed-tail0/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-topk-fixed-tail0/metrics.json). Four cold same-binary 64K/1,024 A1/B1/B2/A2 arms with tail 0, spec 6, MTP max 4 and suffix 0 give **48.128435→49.492594 TG (+2.834413%)**, with TG pairs +1.224207%/+4.478054%. PP mean **−0.143533%**, with both PP pairs negative (−0.255387%/−0.031720%). The before-data gate explicitly required TG ≥1%, both TG pairs positive and aggregate PP ≥−1%; **PASS_NEW_UNPRUNED_FIXED_EPOCH_SCREEN_ONLY**. All four full historical ID arrays and available work match; independent actual-raw review passed 190 checks. The earlier tail7 adaptive strict gate remains FAIL and unchanged. Frozen c183 near-53.75 TG is a different stack/epoch. Cleanup passed, API stayed stopped, and frozen-archive transfer resumed after a network failure without a GPU rerun. No ordinary-profile, full-stack, cross-release or promotion claim.


## 2026-10-11: primary overlap on always-ON REG2/FIT17, negative screen

[Report](results/2026-10-11-gfx906-v0142-topk-primary-fixed-tail0/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-topk-primary-fixed-tail0/metrics.json). Four cold same-binary 64K/1,024 ABBA arms with REG2/FIT17 always ON and only primary overlap OFF/ON measured **49.499129→49.864600 TG (+0.738338%)**, below the fixed +1% mean gate. Both TG pairs were positive (+0.259785%/+1.209908%); PP mean **−0.484817%** passed the −1% floor. All 4,096 historical IDs and available work matched; the independent actual-runtime audit passed 218 checks. **FAIL_PRIMARY_OVERLAP_TG_MEAN_GATE**; the prior unpruned REG2/FIT17 screen winner is retained separately. Two package-copy network failures happened before launch; the third staging attempt launched once. Cleanup passed, API remained stopped, and the maximum final sampled sensor was 54°C. No threshold change, timing retry, promotion or cross-release gain claim.


## 2026-10-11: historical c183 fixed-policy empty-PCIe ablation

[Report](results/2026-10-11-gfx906-c183-empty-pcie-fixed/README.md) · [Metrics](results/2026-10-11-gfx906-c183-empty-pcie-fixed/metrics.json). Four cold 64K/1,024 ABBA arms on the unchanged original c183 full-stack binary, with only empty-PCIe skipping OFF/ON, measured **52.927582→53.909507 TG (+1.855223%)**, with TG pairs +1.872665%/+1.837805%. **First PP pair −1.512460%**; second +0.658765%; aggregate PP **−0.430498%** passes the frozen −1% aggregate floor, which has no PP-pair gate. All 4,096 historical IDs and available work matched; the independent actual-runtime audit passed 327 checks. The first PP-pair cause remains unestablished. **PASS_FIXED_C183_EMPTY_PCIE_ABLATION_SCREEN_ONLY**. ON rates 53.880558/53.938455 re-establish the approximately-54-TG fixed c183 reference. The existing executable was reused for one direct ABBA; cleanup passed, API stayed stopped, and the final sampled maximum was 55°C. No new optimization, new release-port result, threshold change or promotion; earlier failed gates remain unchanged.

## 2026-10-11: historical c183 reversed BAAB PP confirmation

[Report](results/2026-10-11-gfx906-c183-empty-pcie-baab/README.md) · [Metrics](results/2026-10-11-gfx906-c183-empty-pcie-baab/metrics.json). One reversed cold B1/A1/A2/B2 confirmation on the unchanged c183 full-stack binary measured **51.461955→53.903579 TG (+4.744521%)**, with both pairs positive; PP **+0.053321%**, pairs **+0.013129%/+0.093556%**. All 4,096 historical IDs and available work matched; the actual-runtime audit passed 327 checks. The frozen 16-chunk descriptor flags **0 residuals strictly above 500 ms** in every BAAB arm; no timing or arm was excluded or adjusted. All-eight descriptive means are **52.194769→53.906543 TG (+3.279589%)** and **645.616429→644.401038 PP (−0.188253%)**, not a new qualification. The original first PP pair **−1.512460%** remains intact. ON TG is stable across epochs (−0.011%); slower OFF (−2.769%) drives the larger BAAB relative gain. Retain existing empty-PCIe ON at approximately 53.9 TG and end this specific PP-confirmation repeat sequence. **Zero PP loss and universal equivalence remain unproven.** Cleanup passed, API stayed stopped, and the final sampled maximum was 55°C. No source patch, new release result or promotion.


## 2026-10-11: release-local empty-PCIe elision on always-ON REG2/FIT17

[Report](results/2026-10-11-gfx906-v0142-topk-empty-pcie/README.md) · [Metrics](results/2026-10-11-gfx906-v0142-topk-empty-pcie/metrics.json). Four cold same-binary 64K/1,024 ABBA arms, with tail 0 and only elision 0/1 changing, measured **49.846425→50.724083 TG (+1.760725%)**, with TG pairs **+1.811363%/+1.710117%**. PP mean **−0.536465%** passes the frozen −1% aggregate floor; both PP pairs remain negative (**−0.008120%/−1.064662%**) and no PP-pair gate applies. All 4,096 historical IDs and available work match; the independent actual-runtime audit passed 412 checks. B2's third 4K interval accounts for **+1,124 ms of +1,126.1 ms** versus A2; cause remains unresolved, with no exclusion or subtraction. Component admission (8 V1 + 2 V2) and 386-ID guard validation are separate evidence; the V1 late-inspect failure remains disclosed. **PASS_TOPK_EMPTY_PCIE_FIXED_TAIL0_SCREEN_ONLY**. A separate four-process **4K/1,024 and 200,000/256 correctness extension now PASSes**: all **2,560 historical IDs** and fresh paired available work match; the independent actual-runtime review passed **316 checks**. The exact historical 200K fixture bytes were recovered and hash-verified without an alternate-fixture fallback. These unbalanced correctness pairs add no speed claim; selector branch coverage remains source-inferred. Cleanup passed and API stayed stopped; final sampled maxima were 53°C for the 64K screen and 54°C for the correctness extension. No promotion, upstream PR, pooled gain, universal-equivalence or near-54-TG release claim.


## 2026-10-11: v0.1.43 standalone empty-PCIe elision, failed TG screen

[Report](results/2026-10-11-gfx906-v0143-empty-pcie-elision/README.md) · [Metrics](results/2026-10-11-gfx906-v0143-empty-pcie-elision/metrics.json). Pinned v0.1.43 standalone five-file elision port, without REG2/FIT17 or primary overlap: four cold same-binary fixed-tail0 64K/1,024 ABBA arms measured **48.470716→47.980444 TG (−1.011480%)**, pairs **+2.011688%/−4.026131%**. Both TG gates fail; PP mean **−0.227564%**, pairs **+0.072711%/−0.527503%**, passes the −1% aggregate floor. All 4,096 IDs, available work and stable INFO match fresh A1; the actual-runtime audit passed **288 checks**. B2 decode slowdown remains unexplained; PP interval 13 accounts for **+570 ms of +554.8 ms** versus A2. Sparse GPU samples establish no noise/thermal cause; all arms remain. Historical c183 IDs match; the 999-ID difference at index 13 concerns the **original effective-tail7 v0.1.42 B1**, not the [qualified tail0 winner](results/2026-10-11-gfx906-v0142-topk-empty-pcie/README.md), whose report is unchanged. Component and 386-ID guard checks passed separately. **FAIL_V0143_EMPTY_PCIE_TG_MEAN_AND_PAIR_GATES**; broader v0.1.43 prompt qualification pending. Cleanup passed, API stayed stopped, final sampled maximum 53°C. No outlier exclusion, rerun-to-win, cross-version speed claim, promotion or upstream PR.


The same [v0.1.43 report's follow-on decode diagnostic](results/2026-10-11-gfx906-v0143-empty-pcie-elision/README.md#follow-on-decode-diagnostic-prior-slowdown-not-reproduced) adds one predeclared instrumented OFF→ON pair: **2,048 exact IDs/work/INFO**, **379 actual windows** per arm and a **237-check actual audit**. Decode changed **−366.2 ms**; reconstructed outer verify **−363.84 ms**, primary GPU-reach wait **−185.71 ms**, shared CPU **−11.37 ms**. Overlapping mixed-owner buckets must not be summed; rounding is ±1.895 ms per total / ±3.79 ms per delta. No bucket reaches the frozen 620 ms localization descriptor. The old B2 slowdown did not recur and remains unexplained. **The failed ABBA and separate qualified v0.1.42 result are unchanged.** Cleanup passed, API stayed stopped, final sampled maximum 53°C. Diagnostic evidence only; no speed qualification or promotion.


## 2026-10-11: c183 draft-head exposure, below the 1% filter

[Report](results/2026-10-11-gfx906-c183-head-exposure/README.md) · [Metrics](results/2026-10-11-gfx906-c183-head-exposure/metrics.json). Original c183 kernels on draft-owner GPU1: greedy/probability medians **35.141/35.229 us**, pair **70.156 us median / 70.525 us maximum**. A source-derived, unmeasured 1,134-call scenario projects to **79.975 ms / 0.420242% linear wall share** of the historical 19,030.8 ms model reference, below the frozen 1% filter. **DEPRIORITIZE_BELOW_ONE_PERCENT**; park head sampling. Six fixtures and 27 batches passed; the independent actual-runtime audit passed **121 checks**. Conditional synthetic hot-buffer exposure only, not a rigorous critical-path ceiling or measured speedup. Cleanup passed, API stayed stopped, final sampled maximum **47 C**. No optimization or promotion.


## 2026-10-11: c183 NORM_ROPE component repair, park integration

[Report](results/2026-10-11-gfx906-c183-norm-rope/README.md) · [Metrics](results/2026-10-11-gfx906-c183-norm-rope/metrics.json). Original fused finite screen fails on the first case (172 differing FP32 elements); the failure remains. One isolated candidate passes 96 finite cases on both owners; eight nonfinite observations remain outside the contract. All 384 captured timing pairs are positive, but canonical-baseline per-owner exposure is only **20.618–20.801 ms / about 0.109%** in the conditional fixed suffix-OFF scenario. Separate MTP scenarios are not summed across overlapping work. Actual audits passed **119/229/401 checks**. **DEPRIORITIZE_WHOLE_MODEL_PERFORMANCE_PORT**. No engine patch, model speedup, universal-equivalence or causal-proof claim. Cleanup passed, API stayed stopped, final sampled maximum **48 C**.


## 2026-10-11: c183 PP value-load lookahead, negative screen

[Report](results/2026-10-11-gfx906-c183-pp-lookahead/README.md) · [Metrics](results/2026-10-11-gfx906-c183-pp-lookahead/metrics.json). Three finite synthetic full-output/scratch parity cases passed on owner0. The single four-cell value-load lookahead candidate increased captured full-batch median latency **0.754356→0.805721 ms (+6.809112%)**. All eight paired savings are negative, median **−0.051430 ms**, below the frozen **+0.240 ms** conditional PP relevance bar. **REJECT_PP_LOOKAHEAD_PERFORMANCE**; park without an engine patch, model run or variant sweep. All pairs remain; warm repeated-buffer timing is not cold/interleaved model performance. Actual audit **116 checks PASS**; cleanup passed, API stayed stopped, final sampled maximum **46 C**.


## 2026-10-11: c183 Q5 head R2, below the practical filter

[Report](results/2026-10-11-gfx906-c183-q5-head-r2/README.md) · [Metrics](results/2026-10-11-gfx906-c183-q5-head-r2/metrics.json). Five finite synthetic full-output parity cases passed on owner1 across literal archive/new-TU R1/R2 arms. All 72 timing samples remain; **all six T3 pairs regress**. The fixed 379-call/1,247-row scenario spans **48.3479–139.8509 ms / 0.2545–0.7362%**, below the 1% practical filter. **DEPRIORITIZE_BELOW_ONE_PERCENT_FIXED_SCENARIO**; park without T-specific variants, an engine patch or a model run. Original compilation-source identity remains unproven; synthetic component exposure is not model speedup. Actual audit **125 checks PASS**; cleanup passed, API stayed stopped, final sampled maximum **48 C**.


## 2026-10-11: c183 PP shared fork, small descriptive signal

[Report](results/2026-10-11-gfx906-c183-pp-shared-fork/README.md) · [Metrics](results/2026-10-11-gfx906-c183-pp-shared-fork/metrics.json). Observer shared envelopes **2.634/2.060 s** remain separate. V1's scalar-dimension admission bug and unstarted ON arm are preserved. Corrected V2's single ordered OFF→ON pair measured **101,301.5→100,544.3 ms / 646.940→651.812 PP (+0.753101%)**; all 16 integer-progress intervals improved **7–112 ms**. ON joins **432/336**, with **38 MiB extra per owner in both arms**. First-output/work equality only; original serial versus second-handle fork confounds scheduling-only attribution. **PARK_SMALL_DESCRIPTIVE_PP_FORK_SIGNAL**: no qualified speed, full-trajectory, TG or peak-VRAM claim, and no PR. Observer/V1/V2 audits cover **152/172/223 checks**, with an independently verified chunk supplement. Cleanup passed, API stayed stopped, final sampled maximum **54 C**.


## 2026-10-11: c183 prompt F16, approximate exploratory screen

[Report](results/2026-10-11-gfx906-c183-prompt-f16/README.md) · [Metrics](results/2026-10-11-gfx906-c183-prompt-f16/metrics.json). Existing original-c183 HIP_PROMPT_F16 0→1, one fixed-order 64K/one-output pair: **101,333.6→81,985.9 ms / 646.735→799.357 PP (+23.598814%)**, with **19.093075% prompt-wall reduction**. All 16 integer-progress intervals improve **1,087–1,866 ms**. Both first outputs match historical; decode-only cache hits **469→468** differ, while detailed PP route-work equality is unestablished. Approximate rounding, unobserved hidden/logit/output finiteness and one-token scope preclude quality, TG, full-trajectory or qualified-speed claims. Actual audit **223 checks PASS**; cleanup passed, API stayed stopped, final sampled maximum **55 C**. No new build, patch, promotion or PR.


The same [F16 report's 1,024-output follow-on](results/2026-10-11-gfx906-c183-prompt-f16/README.md#follow-on-1024-output-trajectory-diverges) retains a separate fixed-order pair: OFF matches all historical outputs; ON first differs at **index 13**, with **986 mismatching positions**. PP **646.841→799.522 (+23.604045%)**; observed TG **53.92255→55.58722 (+3.087154%)** accompanies different trajectories and work, not isolated acceleration. Accepted/offered **647/868→678/875**; decode cache misses **17,890→30,106**. All 16 PP intervals are faster. Actual audit **223 checks PASS**, cleanup **53 C**, API stopped. Quality smoke remains pending. Quality and full-trajectory parity are unqualified; no further speed runs before quality review, and no PR or promotion.


The same [F16 report's USER-text likelihood diagnosis](results/2026-10-11-gfx906-c183-prompt-f16/README.md#follow-on-narrow-user-text-likelihood-diagnosis-2026-10-12) adds two new public-repository fixtures with **512 scored USER-text targets each**, not an assistant-task benchmark. Primary unconditional NLL increases **+0.531360/+0.255897** (perplexity ratios **1.701245/1.291619**), worsening at **492/386 of 512** positions. Post-run im_end-mass penalties **+0.519265/+0.227216** explain most aggregate shift arithmetically; conditional deltas **+0.012095/+0.028681** do not replace the unconditional results. High OFF/ON argmax agreement is not a quality pass. Actual audit **423 checks PASS** plus independent arithmetic review; cleanup **53 C**, API stopped. No general assistant-quality conclusion or global F16 promotion; assistant-role fixture preparation remains next.


The [assistant-role copy follow-on](results/2026-10-11-gfx906-c183-prompt-f16/README.md#follow-on-assistant-role-supplied-answer-copy-sanity-2026-10-12) adds one easy 4K supplied-answer teacher-forced sanity check: **257/257 assistant targets top-1 in both arms**, mean NLL **0.000148026→0.000176076**, perplexity ratio **1.000028051**; im_end is never top-1. Prior USER-text drift remains unchanged. This is not free-generation, long-context or general-quality qualification. Actual audit **250 checks PASS** plus arithmetic review; cleanup **46 C**, API stopped. No global F16 promotion.


The [bounded 64K free-generation needle follow-on](results/2026-10-11-gfx906-c183-prompt-f16/README.md#follow-on-bounded-64k-free-generation-needle-pass-2026-10-12) passes in both OFF/ON arms: three fixed answers at roughly **10/50/90% depth**, identical **35-token outputs including natural EOS**, with no answer seed. This is one repeated-public-filler task, not three independent samples or broad quality certification. Accepted/offered **26/30** matches, but cache hits **18,139→18,101** differ; no TG benchmark. Actual audit **233 checks PASS**; cleanup **55 C**, API stopped. All prior results remain; no promotion or PR.


The [final 200K needle step](results/2026-10-11-gfx906-c183-prompt-f16/README.md#final-synthetic-retrieval-step-200k-needle-pass-2026-10-12) passes both arms: three fixed answers at roughly **10/50/90% depth**, identical **35-token outputs including natural EOS**. Diagnostic prompt time **325,656.6→268,733.4 ms** and short decode **833.1→1,070.5 ms** are not balanced or TG benchmarks; decode work differs. Actual audit **233 checks PASS**, cleanup **55 C**, API stopped. The synthetic retrieval sequence is complete. All earlier findings remain; exact c183 stays the default and approximate F16 stays experimental, without broad-quality certification, promotion or PR.


## 2026-10-12: PR #2016 cooperative radix scan, gfx906 resource rejection

[Report](results/2026-10-12-gfx906-c183-radix-scan-resource/README.md) · [Metrics](results/2026-10-12-gfx906-c183-radix-scan-resource/metrics.json). A narrow [PR #2016](https://github.com/Niko1221/Strata/pull/2016)-derived c183 candidate fails all six frozen compiler-resource checks: FIT17 scratch **56→84 bytes/lane**, VGPR/SGPR spills **25→36 / 44→67**; guarded REG66 **1,048→1,120**, **468→500 / 539→549**. The inherited 13-symbol assumption was wrong: exact production has **12 kernels / 10 unchanged**, with historical-only block_scores_simt_kernel absent. Original failure remains intact; accounting correction does not remove resource rejection. Independent actual review verified **38 file hashes** and bounded ISA observations. **Park before GPU execution**; no measured slowdown, runtime correctness, model integration or rerun. Upstream other-hardware results are unaffected.


## 2026-10-12: prompt-F16 first-16 HumanEval pilot

[Report](results/2026-10-12-gfx906-c183-prompt-f16-humaneval-pilot/README.md) · [Metrics](results/2026-10-12-gfx906-c183-prompt-f16-humaneval-pilot/metrics.json). Original c183 OFF/ON both pass **16/16 base and 16/16 base+extra** on fixed HumanEval/0–15, with **32 natural completions** and no failed/timed-out statuses or paired outcome changes. **Six solution texts differ**. Actual generation/evaluator seals bind the samples and results; earlier setup, generation and evaluator infrastructure failures remain separate. This is a bounded **16-of-164 pilot**, with no broad-quality or speed claim. Earlier F16 findings remain intact; exact c183 stays default and approximate F16 experimental. No solution contents, promotion or implementation PR.


## 2026-10-12: prompt-F16 balanced ABBA and experimental-option verdict

[Report](results/2026-10-12-gfx906-c183-prompt-f16-abba/README.md) · [Metrics](results/2026-10-12-gfx906-c183-prompt-f16-abba/metrics.json). Fixed 64K/1,024-output ABBA gives mean PP **645.255→796.657 tokens/s (+23.4639%)**, with pair gains **+23.3093% / +23.6177%**; the frozen ≥1%-mean/both-positive criterion passes. Both OFF runs match historical output and each mode reproduces its 1,024-output trajectory and available counters. Cross-mode divergence remains **index 13 / 986 differences**. TG **+3.0366%** is changed-work descriptive only. Actual audit verifies **64 collected file hashes**, cleanup **53 C**, API stopped. Narrow HumanEval/copy/retrieval passes coexist with earlier USER-text likelihood drift. **Exact c183 remains default; existing approximate F16 stays optional and experimental**, without broad-quality certification, new implementation PR or planned further GPU tests.


## 2026-10-12: GEMM output diagnosis and signed-FIRST4 rejection

[Report](results/2026-10-12-gfx906-c183-gemm-output-diagnostic/README.md) · [Metrics](results/2026-10-12-gfx906-c183-gemm-output-diagnostic/metrics.json). Four signed-FIRST4 FP32-output candidates pass full-bit parity on one deterministic narrow-range fixture, but **all 32 timing pairs regress**: candidate medians **29.784–33.656 ms** versus references **15.058–15.188 ms**. **55 returned solutions remain untested**. V1's positive-only filter selected zero alternatives and remains recorded separately. FP16 round/widen changes **10,483,999 / 10,485,760** values; actual FP16 output differs from the rounded reference at **73,709 positions**, without isolating an internal cause. Both actual audits pass; V2 cleanup **46 C**, API stopped. **Park without integration**; no universal exactness, model-quality or model-speed claim. Existing F16 verdict remains unchanged.


## 2026-10-12: remaining-main-BF16 exposure observer

[Report](results/2026-10-12-gfx906-c183-pp-bf16-exposure/README.md) · [Metrics](results/2026-10-12-gfx906-c183-pp-bf16-exposure/metrics.json). One 64K/one-output F16-OFF observer run identifies HC injection as the largest selected family: **3,443.181 ms / 864 calls** primary and **2,671.397 ms / 672 calls** peer, shape **N4/K10,240/T4096–4095**. The primary **3.390%** pinned-reference time proxy is **not a gain**. Owner totals **7,276.479 / 4,728.024 ms** remain separate; nested intervals include host gaps. Standalone MTP and optimized HC down/up are excluded. Actual audit **285 checks**, **4,640 calls**, event highwater **8/6**, cleanup **54 C**, API stopped. Source investigation only; no tensor capture, exact-conversion or optimization result.


## 2026-10-12: HC injection input-exact route rejected; diagnostic incomplete

[Report](results/2026-10-12-gfx906-c183-hc-inject-exact/README.md) · [Metrics](results/2026-10-12-gfx906-c183-hc-inject-exact/metrics.json). All **96/96** finite ordinary actual-weight cases accept operand guards but fail output parity: **1,519,845 / 1,572,864 FP32 elements differ (96.629143%)**. Direct BF16 control and two subnormal one-hots pass. After **98 partial parity records**, an unexplained guard assertion aborts the probe with **exit 1**; T4095, adversarial results, fallback completion and timing remain untested. Actual audit validates partial evidence only; **no speed or error-magnitude/model-quality result**, cleanup **46 C**, API stopped. Route rejected without integration. Observer caveat corrected in this report: excluded HC down/up was only **partially taken** (combined takes/attempts **531/1,728 primary; 567/1,344 peer**); its remaining fallback exposure was not measured.


## 2026-10-12: HC injection N4, V1 rejection and V2 component speedup

[Report](results/2026-10-12-gfx906-c183-hc-bf16-n4/README.md) · [Metrics](results/2026-10-12-gfx906-c183-hc-bf16-n4/metrics.json). Both BF16 candidates pass **214 cases / 3,505,748 finite FP32 elements**, with controls and pre/post-timing checks. **V1 remains slower in all 32 event/wall pairs**, candidate/reference median-time ratios **2.589–2.644×**. Cooperative-K16 **V2 is faster in all 32 pairs**: **3.990–4.000→0.959–0.965 ms**, reference/candidate median-time ratios **4.14–4.17×**. The complete two-kernel path preserves the pinned GSU3/FMAC/reduction schedule and FP modes. Actual audits **287 checks each**, cleanup **47 C**, API stopped. Earlier scaled-FP16 rejection remains distinct. Finite warmed component evidence only; **no universal exactness, model-quality or end-to-end gain claim**, integration or promotion implied.


## 2026-10-12: HC injection N4 shadow and 64K model ABBA

[Report](results/2026-10-12-gfx906-c183-hc-bf16-n4-model-abba/README.md) · [Metrics](results/2026-10-12-gfx906-c183-hc-bf16-n4-model-abba/metrics.json). Same-derived-binary ABBA measures PP **646.882607→664.842326 tokens/s (+2.776349%)**, both pairs positive; mean prompt time saves **2,736.75 ms**. All four **1,024-output trajectories and available work counters match historical controls**; ON retains candidate output for **1,536 calls**, shadow OFF. TG **−0.110912%**, ratio **0.998890879**, passes the frozen **0.99** practical tolerance. Separate reference-output-preserving shadow finds **zero differences across 1,536 calls / 25,165,440 FP32 elements**. Actual audits **306/585 checks** pass. Pinned c183/gfx906/rocBLAS-GSU3 opt-in scope only; global prompt-F16 OFF. No universal exactness, broad-quality or default-promotion claim; other context lengths remain separate.


## 2026-10-12: later HC N4 caveat, reverse-block TG loss and length checks

[Report](results/2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/README.md) · [Metrics](results/2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/metrics.json). **Reverse BAAB TG falls 1.612671%**, ratio **0.983873293**, below the earlier **0.99** tolerance; the last pair retains **−2.864378% / +559.9 ms decode**. PP remains **+2.645645%**. Original ABBA is unchanged. All eight arms are retained and historical output/work-exact; pooled **PP +2.711000%, TG −0.862031%, +167.725 ms decode** does **not erase the reverse-block failure or prove zero loss**. Separate 4K/200K pairs pass output/work exactness with descriptive timing only; 200K retains 96 baseline tail fallbacks. Cause remains unresolved under sparse telemetry. Actual audits **669/722 checks** and cleanup pass. No replacement qualification or default promotion.


## 2026-10-12: decode diagnostic did not reproduce prior HC N4 slowdown

[Report](results/2026-10-12-gfx906-c183-hc-bf16-n4-decode-diagnostic/README.md) · [Metrics](results/2026-10-12-gfx906-c183-hc-bf16-n4-decode-diagnostic/metrics.json). One diagnostic OFF/ON pair gives decode **19,006.0→18,971.4 ms (−34.6 ms)**; the earlier four negative TG pairs **remain unchanged and unexplained**. Across 379 windows, verify changes **−34.11 ±3.79 ms**, commit/draft each **0 ±3.79 ms**, residual **−0.49 ±11.47 ms**; these are rounding bounds. Full historical outputs/work match. Existing post-decode printing adds no new GPU events. The bound interpretation addendum corrects nested fields to **mixed primary-Verifier/shared-Drive scope**, not additive owner GPU time. Actual audit **324 checks**, cleanup **53 C**, API stopped. No fix, zero-loss proof, replacement qualification or further repeat is claimed.


## 2026-10-12: verify-boundary observer, earlier TG losses still unresolved

[Report](results/2026-10-12-gfx906-c183-verify-boundary/README.md) · [Metrics](results/2026-10-12-gfx906-c183-verify-boundary/metrics.json). One changed-host diagnostic pair gives decode **19,494.2→19,000.8 ms (−493.4 ms)**; **the four prior negative TG pairs remain unresolved**. Outer verify changes **−502.016149 ms**, including nested primary wait **−285.049571 ms** and inclusive peer **−53.849778 ms**. Cold primary T2 instantiate/destroy differs **196.170272→8.029045 ms**, while the other 47 T2 windows are nearly equal. A separate later OFF T4 maximum **338.061519 ms** lacks an owner-level causal join. All capture spans differ **−158.497496 ms**; subtracting them is not a warm benchmark. Historical output/work equality and 379 windows hold; actual audit **532 checks**, cleanup **52 C**, API stopped. No fix, zero-loss proof or replacement performance qualification.


## 2026-10-12: joined observer and peer-affinity single-pair CPU trade-off

[Report](results/2026-10-12-gfx906-c183-peer-affinity-screen/README.md) · [Metrics](results/2026-10-12-gfx906-c183-peer-affinity-screen/metrics.json). With N4 ON in both affinity arms, the screen gives **PP +1.504940%, TG +0.080068%**, but peer-caller CPU rises **40.417→74.376 s (+33.958774 s, +84.020945%)**; this excludes child/helper threads and is not energy or useful-compute accounting. All 16 task/progress intervals improve, masks restore, and historical outputs/work match. Earlier joined-observer V2 retains its weaker **PP +0.426873%**, including the **+2,139±2 ms** second progress interval; no interval is excluded. Current inventory cannot establish historical pressure, and kernel-log access was denied. **Prior four N4 TG losses and stalls remain unresolved.** Audits **1,128/29/412 checks** pass. Single-pair screening only; the separate eight-arm qualification has no result in this report.


## 2026-10-12: combined N4 + peer-affinity eight-arm qualification

[Report](results/2026-10-12-gfx906-c183-peer-affinity-combined/README.md) · [Metrics](results/2026-10-12-gfx906-c183-peer-affinity-combined/metrics.json). Fixed same-binary A=N4 OFF/affinity OFF versus B=both ON passes both frozen blocks: **ABBA PP +4.266646%, TG +0.521840%; BAAB +3.745738%, +0.081620%**. Pooled **PP +4.006136%, TG +0.301892%** retains all eight exact-output/work arms. **Two TG pairs still regress (−0.034220%, −0.293685%)**, and mean peer-caller CPU rises **79.990869%**, excluding descendants/helpers. Native PP+decode/request means fall **3,962.1/3,958.404 ms**. Actual audit **1,402 checks**, verified treatment/masks/censuses and cleanup **53 C** pass. Combined historical-profile qualification only: **no statistical zero-loss, separate-component attribution, current-main port admission or default promotion**. All earlier negative results and report epochs remain intact.


## 2026-10-12: historical c183 winner preservation checkpoint

[Checkpoint](results/2026-10-12-gfx906-c183-winner-preservation/README.md) · [Manifest summary](results/2026-10-12-gfx906-c183-winner-preservation/metrics.json). The historical **672.137076 PP / 53.728913 TG** result is retained unchanged. Independently verified private off-machine copies secure both executables, **26 compiled-project payloads / 11 literal winning link inputs**, and **30 exact campaign source/patch/receipt files**, alongside all original raw results and actual launch controls. Full Git history/checkout, complete external dependencies/image and a recovery rehearsal are not claimed. No new benchmark, binary publication, default promotion or replacement of prior results.


## 2026-10-12: fresh-main N4 validation retains failed performance qualification

[Report](results/2026-10-12-gfx906-a0116b2-n4-validation/README.md) · [Metrics](results/2026-10-12-gfx906-a0116b2-n4-validation/metrics.json). **Fresh-main performance qualification fails:** BAAB TG **−0.138327%**, ratio **0.998616728 < 1.0**, despite PP +2.001407%; pooled PP/TG **+2.240104%/−0.060944%** cannot rescue it. All eight outputs/work/capacities match. Build/V3 identity, six CPU CTests, **20 component cases / 327,640 FP32 elements**, and reference-preserving **1,536-call / 25,165,440-element shadow** pass within their scopes. Separate six-arm correctness passes, retaining **4K TG −3.187818344% / +655.9 ms decode** and the small 200K loss. A later one-pair diagnostic instead finds OFF slower by **2,266.3 ms**; its outer verify aggregate does not establish a cause or fix. All prior epochs and the preservation checkpoint remain unchanged. **No qualified-speedup, zero-loss, default-promotion or ready-PR claim.**


## 2026-10-13: REG2 / FIT17 selector builds and bounded component checks

[Report](results/2026-10-13-gfx906-a0116b2-selector-components/README.md) · [Metrics](results/2026-10-13-gfx906-a0116b2-selector-components/metrics.json). Fresh B0/S1(REG2)/S2(REG2+FIT17) builds and later linked-image/ISA review pass. **Owner0 passes 528 case records on original harness executables; corrected owner1 passes 528 on new executables**, each variant 88 direct + 88 graph replays. The original device1 attempt remains a **zero-case native CLI refusal**, not a parity failure. One host-TU correction and three relinks preserve fixture/default-0 behavior, selector GPU images and engines; actual ordinal1/physical-device binding is verified. FIT17 retains **56 B private scratch / 25 VGPR spills**. **Executed device body was not observed; model/performance qualification remains pending.** Existing #1535/#1743 attachment evidence only; no benchmark timings, duplicate PR or user-edited PR-body change.


## 2026-10-13: REG2 + FIT17 selector eight-arm model qualification

[Report](results/2026-10-13-gfx906-a0116b2-selector-qualification/README.md) · [Metrics](results/2026-10-13-gfx906-a0116b2-selector-qualification/metrics.json). **Both frozen blocks pass:** ABBA **TG +1.087012%, PP −0.012001%**; BAAB **TG +2.468158%, PP +0.753949%**. TG required ≥1% mean gain and both pairs positive; **PP permits up to 0.5% mean loss**, not zero loss. All eight full outputs/work/capacities match. Pooled TG **48.313073→49.171839 (+1.777504%)**, PP **581.894568→584.045236 (+0.369597%)**; request mean **−774.713 ms**, but **load plus request +6.550 ms**. Earlier 4K/32 correctness retains **TG −1.024931% / +7.4 ms decode**. Actual audit **1,035 checks** plus raw load readback, cleanup **52 C**, API stopped. This advances the preceding component report's pending-model status for the pinned combined B0/S2 profile only. **No isolated REG2/FIT17 attribution, observed device-body route, default promotion or universal/statistical zero-loss claim.** All prior N4 failures and report epochs remain unchanged.


## 2026-10-13: Q2 grouped-expert component correctness on both owners

[Report](results/2026-10-13-gfx906-a0116b2-q2-components/README.md) · [Metrics](results/2026-10-13-gfx906-a0116b2-q2-components/metrics.json). **144 finite cases / 864 grouped calls pass** within the same Q1 executable across two MI50 GPUs, covering mode 7→13 gate/up, 13→15 down-only and full 7→15 comparisons. Six shapes, four group plans and three grids retain byte parity, q8 metadata, write/guard/input checks; both exits and cleanup pass, final **45 C**, audit **255 checks**. Original component baseline-preservation/model-admission false flags remain intact. Separate bounded mode7 static evidence and a current **48-layer / 144-tensor** metadata census cover their stated shape/format scopes; **the other 151 changed baseline device bodies remain outside equivalence proof**. No observed per-call device route or performance timing; **model results and performance qualification remain pending**.
