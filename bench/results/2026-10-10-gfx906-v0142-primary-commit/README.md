# v0.1.42 primary-commit overlap: technical PASS, scientific FAIL

## Result

**The fixed performance screen failed. No qualification, retry or promotion.** TG improved 1.242043% in the mean and both matched pairs were positive. The first PP companion pair regressed 0.186609%, violating the unchanged nonnegative companion-pair condition. Mean PP improved only 0.293981%. Exact outputs, available work, capacities and the reviewed lifecycle checks passed.

| Native-counter metric | OFF mean, tokens/s | ON mean, tokens/s | Mean change | Forward/reverse pair changes |
| --- | ---: | ---: | ---: | --- |
| PP | 621.816996 | 623.645018 | +0.293981% | -0.186609%, +0.778720% |
| TG | 51.088791 | 51.723336 | +1.242043% | +1.226761%, +1.257351% |

The predeclared gate required at least 1% mean PP or TG gain, positive matched pairs for the winning metric, and nonnegative companion mean and both pairs. TG's combined gate therefore fails despite its positive gain; PP is below 1% and has a negative first pair. No observation was excluded, tolerance added, or rerun used to rescue the result. Two clean observations per arm do not establish significance or broad performance.

## Release-local source and build

This is a three-file host-side primary-commit change on release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, with llama.cpp `3cf03257f219afbe7334045ff7c6a06ac68c627d`. Source review checked the context-only port against its donor, default-OFF behavior, eligibility, ownership and drain paths. It included 66 compiled mock eligibility cases, 16 abstract fault-model cases, and nine release-context tests. Those tests are not GPU fault injection.

The candidate compiled in 394.729328 seconds with 191 compile commands. Baseline executable SHA-256: `572c7fb33c95d8b5c16803a8550abeab13eeccb9314136ae101ce61ecd605171`; candidate: `3f96e7dc01728e49723ac3a6e91567d77557c65f59b05cea6083d98d464e3996`. Host ABI/layout and added checks are not claimed byte-identical or zero-overhead.

**Raw device ELF byte equality failed and remains false.** A separate strict structural proof admitted only explicitly established per-translation-unit CUID names and corresponding string/symbol/hash bookkeeping differences. Every other byte and relocation-symbol relationship was checked. Exact instruction/global-data/ABI/resource content was established across 61 device-object modules, 1,901 kernel descriptors, 56 linked engine modules and three linked probe modules. Independent testing rejected 1,299 mutations. No binary was rewritten and the raw mismatch receipt was not relabelled as equality. Build success by itself did not establish overlap correctness or speed.

## Controls and fixed method

Order: **QBASE, QOFF, QON, QSYNC, A1, B1, B2, A2**. Eight distinct native processes served **12 requests**, with **4,612 total output tokens verified** within matching request groups.

Each of the four diagnostic processes served a cold 4,096-token prompt for 128 outputs, then another cold request for one output using the same engine/verifier resources. QBASE used the pristine release; the other diagnostics used the candidate. QOFF left overlap unset. QON enabled overlap and trace. QSYNC enabled overlap but set `STRATA_COMMIT_SYNC=0`: this flag is presence-based, so even value 0 forces synchronous behavior. Likewise, overlap value 0 would enable it; runtime OFF must unset the variable.

Clean A1/B1/B2/A2 used the same candidate executable, fresh 65,536-token prompts and 1,024 outputs, with all traces absent. A left overlap unset; B set `STRATA_PRIMARY_COMMIT_OVERLAP=1`. Query swizzle and reduce12 stayed ON throughout; top-k and other c183 treatment bundles were absent. Sampling and capacities followed the validated release-local profile. There was no profiler or affinity change. Diagnostic durations were excluded from performance; the pristine-release diagnostic does not establish throughput equivalence.

## Actual queue/drain and parity evidence

QON's first request recorded **39 queues and 44 successful drains**: 39 queued drains plus five no-queue self-commit drains. The second, single-token request recorded **zero queues and one no-queue drain**. QOFF and force-sync QSYNC recorded eligibility 0 and zero queues/drains. Prefix checks found no pending ownership at DONE or before the next request. Final suffix summaries printed after DONE were reconciled, and all clean timing arms were trace-free.

These are source-bound host queue/drain observations, not per-device kernel counters or a measurement of overlap duration. The `drafted1` marker can include skipped drafts, so it does not prove actual draft execution. Actual EOS paths, GPU fault injection and failure-path recovery were not exercised. Resource reuse with cold prompts is not conversation-cache reuse or production restore coverage. Prefix snapshots and program order establish the checked boundary; precise cross-stream stdout/stderr timestamp ordering is not inferred.

All 12 requests passed full output-ID, available-work, cold-prompt and capacity checks within their matching groups. The clean timing work was accepted/offered 678/862, cache hits/lookups 548429/569246, suffix windows/accepted/offered 2/3/8, prompt_read 65536 and prompt_reused 0. Five unavailable optional chain counters remain null. Release-observed capacities were stable, including 19,078 total / 9,900 primary expert slots, 32,400 MiB arena, and 15 pool workers. No historical c183 outputs or speed gains were imported.

## Safety, timing, and limits

Actual execution was **2026-10-10 20:32:38.383954–20:46:58.165142 UTC**. Owned process/executable/environment and CPU0/thread identities were checked across requests. All 182 raw GPU observations stayed within reviewed limits, with a minimum 9°C margin and peak sensor 81°C. High mode and 190 W caps were unchanged. Final owned cleanup passed; the container query was empty, GPUs reported 0% busy, and the API remained stopped.

This single fixed screen covers the candidate OFF/ON profile on the dual-gfx906 test server. It does not qualify production readiness, 200K prompts, arbitrary fault recovery, or a cross-release improvement. Existing attention results are not added to the descriptive TG number, and no top-k effect is included.

## Evidence seals

Full numerical metrics, trace counts, source/build provenance and audit limitations are in [metrics.json](metrics.json). Private paths, process identifiers, model payloads and raw traces are omitted. The runtime receipt archive contains 121 regular members, 1,866,956 uncompressed bytes and 244,736 compressed bytes.

- Source audit: `ae69d2a5ece465d66277db5c5f59419eccb55a6b1efb6440115bd89cb3457add`.
- Build audit: `dce3f9e1fc106b3d7bea16d4ed36c073433a662092b3dfc82ae19c410c671abd`.
- Structural device proof: `e1f5df122cc78b68cc80bd29eb2bb4361eeed478ee82dd976e61d61292294198`.
- Independent proof review: `2f7dbeedd95539fe3e6923e50a4a2e7e57277a32917c575afe6cbfbd613b6baa`.
- Actual runtime audit: `b4dfa2cf0d9af4d825af19b7d219f738879e94be83bdb09a45c0302ed9b9e8bf`.
- Core numeric audit: `e7e9d656766a862a80b3ad37fb98c5f82b1855c7a610c3241106a1e2b23dc0c0`.
- Runtime archive: `a24f5cceb4aae9ae01dd4c13bcec96972c5adb01fde9706e4875d6642d3f1983`.
