# Empty-PCIe observer: preserved V1 failure and V2 local diagnostic

## Finding and scope

**V2 passed the exactness, diagnostic-quality and local heuristic checks. Its conclusion is only “local source proposal worth reviewing.” Optimization qualification and promotion remain false.** The three fresh OFF1 / OBS / OFF2 processes each completed a cold 65,536-token input and 256 outputs with all full IDs, available work and capacities identical.

The sparse observer produced **372 records at four sites, 93 windows per site**, with **zero nonempty records**. Each site's zero-count, ready-before-group subset had median local group bracket **29.12 microseconds**; the 95th-percentile adjacent-marker spacing over complete windows was **3.04 microseconds**. Their ratio was 9.578947 at each site. These same-owner local measurements justify reviewing a narrowly scoped source proposal; they do not measure removable time or model speedup.

Original waits remain in place. At the post-group / pre-wait sample, the original readiness predicate was still false in **4/93, 6/93, 5/93 and 0/93 windows**. A future proposal must preserve readiness, count and ownership behavior. Sampled false predicates are not wait-stall durations. No cross-owner clock subtraction, 48-layer extrapolation or global gain is claimed.

## V1 failure was retained, not hidden

V1 ran on **2026-10-10 22:44:09–22:47:04 UTC**. OFF1 completed; OBS returned `empty PCIe observer: gfx906 HIP build required` before observer initialization, allocation or marker launch. OBS emitted zero tokens and no DONE/observer records; OFF2 was not launched. Normal model/GPU initialization and OFF1 work did occur. V1 is an implementation/host-eligibility failure, not a negative latency or overhead measurement. Its cross-arm parity, quality and local statistics remain unavailable rather than zero or passed.

The host begin guard incorrectly required `STRATA_USE_HIP`, absent from the actual host compile definitions. The earlier host-support test explicitly defined that macro alongside `STRATA_HIP_GFX906`, masking the real build combination. V2 corrected only the host guard to the reviewed `STRATA_HIP_GFX906` convention, without a global backend-macro or device-source change. Independent real-header compile and actual host-control-flow proofs checked reachability and failure exits. V2 used fresh OFF endpoints; V1 timing was not reused.

Prelaunch and receipt-transfer errors from V1 remain separate transport evidence. Transfer-only recovery did not repeat native work. V2 was a separately reviewed corrected diagnostic, not an unreported rerun to select a favorable timing.

## V2 measurement and quality

Actual V2 execution was **2026-10-11 00:16:40.968094–00:23:47.786612 UTC**. Some artifact names retain the preparation date 20261010; they do not change the execution date.

| Arm | PP tokens/s | TG tokens/s | Decode ms |
| --- | ---: | ---: | ---: |
| OFF1 | 626.046021 | 47.930202 | 5341.1 |
| OBS | 626.386493 | 47.804896 | 5355.1 |
| OFF2 | 626.114804 | 47.948156 | 5339.1 |

OFF endpoint symmetric variation was **0.010986% PP** and **0.037452% TG**, within the frozen 0.5% limits. OBS decode time was **15.0 ms / 0.280894% longer** than the OFF mean of 5340.1 ms, within the 1% absolute diagnostic budget. These quality checks are not performance qualification or a causal upper bound on instrumentation cost. Marker launches/stores, ring bookkeeping and checked per-window current-device host queries may perturb execution.

| Site (device, layer, ring) | Ready before group | False at pre-wait sample | Nonempty records |
| --- | ---: | ---: | ---: |
| 0, 0, 1 | 88/93 | 4/93 | 0 |
| 0, 3, 4 | 85/93 | 6/93 | 0 |
| 1, 27, 1 | 86/93 | 5/93 | 0 |
| 1, 28, 2 | 93/93 | 0/93 | 0 |

The wall-clock rate was queried as 25,000 kHz for each owner; it is not the GPU core frequency. The pooled heuristic requires at least 32 complete windows, 16 zero-count ready-before windows, no nonempty records and median bracket strictly greater than three times the adjacent-marker p95. All four sites passed. Per-T counts were 12/10/7/64 for T=1/2/3/4. Smaller per-T groups do not independently meet the sample-count gate; their summaries and failure flags are retained in metrics. The 6.4-microsecond median wait-containing bracket is also a bracket, not a measured pure stall duration.

All 768 output IDs were checked. Available work was accepted/offered 164/216, cache hits/lookups 143332/146623, full prompt read 65536 and reuse 0; suffix summary was absent. Optional chain counters are unavailable in the 16-field native protocol. The 93 windows cover 257 committed keeps with final keep 4, clipped to 256 emitted outputs. The observed route was pcie_mode=2, device_plan=0, shared_stream=1, df_branch=0, split=0 and GU/down=42. Other layouts, nonempty routes and formats were not demonstrated.

## Source and static identity limits

Release: `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`. V2 executable SHA-256: `67c9fc5af0c694c4af0eca859ea78505e09be7a54f37a712c4a77f41f518caf4`. Query swizzle and reduce12 stayed ON in all three arms; only the observer switch varied.

Against V1, all 61 device payloads and three linked fatbins are raw-identical. Against pristine release, raw payload and original-instruction equality remain **false**. Separate proofs account for four exact PC-relative literal fields (seven differing bytes) and derived descriptor entry offsets, preserving targets, original kernel/data/ABI/resources and control flow. The observer entry is the only added device entry. No blanket normalization or rewritten raw-equality claim is used.

The compile-only stage attempted CMake GPU discovery and found no device; zero discovery API calls is not claimed. Omitted target source trees, compiler/runtime bytes and full preprocessed text were not independently rehashed on the controller: their provenance rests on the pinned-image helper, sealed recipes and successful pre/post integrity checks. The actual host field/type/enum relationships and control flow were audited; independent vendor layout reconstruction was not claimed. Inherited device restoration calls are not all individually status-checked, so general fatal-GPU recovery is outside scope.

## Safety and audit coverage

Within each V2 process, all 28 READY/DONE thread identities and affinities matched. There were 86 raw GPU snapshots; peak sensor temperature was 81°C and final maximum 53°C. High mode and 190 W caps were unchanged; cleanup passed, final containers were absent, GPUs reported idle and the API remained stopped. CPU evidence is endpoint identity/affinity, not continuous CPU sampling. Terminal snapshots do not establish continuous state after collection. No EOS, multi-request reuse or fault-injection claim is made.

The independent audit verified the 39-member V2 archive and transfer, exact raw/derived observer fields and per-T summaries, and rejected 1,129 malformed-record, counter and protocol mutations. An initial reviewer negative test mistakenly treated accepted=163 as invalid marker coverage; tail clipping allows it, so it was retained as a positive control and accepted=162 used for invalid short coverage. Actual accepted=164 remains bound to all three native DONE records. Initial test evidence was preserved; no raw data, implementation or thresholds changed.

## Evidence

[metrics.json](metrics.json) retains sanitized numerical detail, per-site/per-T summaries, source/build identities, V1 failure and limitations. No private host paths, PIDs, raw model payloads or credentials are published.

- V1 failed-runtime audit: `3742c6fb1a7e533c4d43958667b155130973a7c4b6dc3996da1029a32ab2323d`.
- V2 build audit: `c5c057bf395cd4009e0f45406b698d264aa78472a1c183d60312c0ae32a9a1fe`.
- V2 actual audit: `49585758de7a7419bc3d4750a9c5c4d6369b3e76b17251921e85d78c3dd9243e`.
- Recomputed metrics: `1aeabce94c73d8b9dd48270fae3f38b2fd47f3ba0b070f099847839c709aaa62`.
- Observer detail: `4f2802f358380a6b5f753619c9c5da536647fd69b1dbce172f27490f82b40362`.
- V2 raw archive: `945164a61a4e4b481773062ef693e48f32c5e9af3ae31de4af6e3033ef0236eb`, 282,605 compressed bytes, 39 regular members / 2,779,102 uncompressed bytes.
