# Prefill existing-wait attribution: diagnostic only

**DIAGNOSTIC_ONLY; no performance qualification.** The six instrumented existing wait sites account for **17.574090553 CPU-s**, or **10.336731%** of **170.015937957 stage-thread CPU-s**. The remaining **152.441847404 CPU-s is unclassified**. It includes instrumentation and unmeasured work; it cannot be labelled useful computation, launch overhead, hidden waits or GPU time. This measurement does not repair the [previous rejected CPU1 placement screen](../2026-10-10-gfx906-peer-prefill-cpu1/README.md).

## Method and binding

One cold 65,536-token / 1,024-output diagnostic used the reviewed CPU1 placement, default 20,000-us pool spin, unchanged residency/workload and bounded existing-wait instrumentation. Role/decode/split timing was off. No waits, kernel work, affinity changes or reordered operations were added by this instrumentation; original checked/ignored API return handling was preserved. Thread-CPU and monotonic wall clocks measure time inside six existing sites. Same-thread nesting is rejected; aggregate logs do not retain every individual call interval.

The build independently reproduced original c183 and the exact placement-only control, then added only sync instrumentation. All 55 device modules were identical and executable checks passed. The instrumented binary SHA-256 is 19522cc6460c2d33d56ef3b44d17bd5db46a3c7889a427d5c3854bb1642ed275. Source, three-stage build, runner and actual-audit seals are retained in [metrics.json](metrics.json).

Actual evidence contains **17 stage scopes / 130 bucket rows**: one primary 65,535-token run and sixteen peer chunks (15 × 4,096 + 4,095 tokens). Site counts matched the reviewed grouped-MMQ route. Buffers were bounded at 32 scopes / 128 buckets each, without hot-path logging or allocation. Buffered output was flushed after the existing pipeline drain, before prompt timing ended.

## Measured thread-CPU accounting

| Stage device | Enclosing CPU, s | Existing wait-site CPU, s | Unclassified residual, s |
| --- | ---: | ---: | ---: |
| 0 | 93.490604484 | 9.838013219 | 83.652591265 |
| 1 | 76.525333473 | 7.736077334 | 68.789256139 |

Site totals below sum calls across both stage devices. Wall sums are accumulated site durations, **not elapsed pipeline time**; stage threads overlap.

| Existing site | Calls | Thread CPU, s | Accumulated wall, s |
| --- | ---: | ---: | ---: |
| issuer-ready yield loop | 114,127 | 0.076539101 | 0.590388581 |
| router-ready compute-stream sync | 768 | 15.003013805 | 15.011610439 |
| primary handoff sync | 16 | 1.350948356 | 1.351162247 |
| terminal peer chunk callback sync | 16 | 1.143501391 | 1.143550788 |
| run-tail compute-stream drain | 17 | 0.000028531 | 0.000057631 |
| run-tail copy-stream drain | 17 | 0.000059369 | 0.000059085 |

The measured share describes only these observed host sites in this run. It is not a CPU-busy-wait fraction for the whole process, a GPU-idle fraction or a removable critical-path saving. Time inside an API does not identify its internal reason for consuming CPU.

Coverage is limited to six sites in prefill.cpp. Nested GEMM guard code in the exact c183 source has an uninstrumented 40-byte pageable-stack cudaMemcpyAsync followed by cudaStreamSynchronize under the active scale-probe/exact-input path. Those nested calls are outside these buckets. The residual is therefore not non-synchronization time; their current CPU contribution or proportion was not measured by this diagnostic.

## Pipeline timing, checks and limits

Main-scope wall time was **94.475046155 s**; complete pipeline span was **99.740547885 s**, with final peer completion **5.265501730 s** after main exit. Summed cross-thread wall scopes must not replace that span. Diagnostic prompt time was 99,939.5 ms and includes buffered flush; decode was 19,034.8 ms. Neither is a speed comparison.

All 1,024 IDs and available historical work counters matched exactly. Five optional counters remain unavailable, not zero. All 17 scopes had sparse placement observations; within this one run, all 28 persistent thread identities and their READY/DONE affinities matched. Twenty-four observations and 0.295081777 s observed read overhead do not establish continuous placement or total measurement perturbation.

Independent actual audit verified 19 regular raw files, scope/site arithmetic, placements and cleanup. Peak captured temperature was **79 C**, final maximum **51 C**. No promotion, deployment or performance qualification resulted. Raw archive: 60,717 bytes, SHA-256 b6ed34057118ce95d48402e8fceab977ece0e37814e00e3869ae3751a1ac9e1c. Actual-audit SHA-256: f6e8df517140aad10429b4d9c94fd12745d4fd3ab452129fcda2bcbb1939f521.

Only this report, numerical metrics and archive index are proposed for publication. Private paths, raw logs, process identities, credentials and model payloads are excluded; hashes identify private retained evidence rather than a standalone reproduction package. Runtime code, PR bodies and the earlier screen's failure remain unchanged.
