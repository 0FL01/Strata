# CPU pool spin: parked after a fixed 64K ABBA regression

**PARK_POOL_SPIN_100US.** Reducing the frozen c183 CPU pool's spin interval from its default 20,000 microseconds to 100 microseconds produced **+0.018434% PP / -2.085543% TG** in one fixed 64K/1,024-output ABBA. Both TG pairs regressed (-2.309717% and -1.861248%). Full token IDs, available counters and checked affinity matched; the independent actual-receipt audit passed. The performance gate failed. No tuning, rerun, promotion or deployment follows.

## One controlled setting change

All five fresh processes used the same frozen c183 executable, SHA-256 c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049. The schedule was diagnostic D0, then A1/B1/B2/A2. Each used the fixed cold 65,536-token fixture, 1,024 greedy output tokens, seed 12345, unchanged residency of 19,078 (9,900 + 9,178), topology and affinity, and adapt-every 0. This is a comparison within the retained combined c183 R&D control, not stock upstream or a change to the stable ce deployment.

A1/A2 retained the 20,000-us default; B1/B2 added only STRATA_POOL_SPIN_US=100. The actual owned process environment, executable hash and affinity were bound once before generation in every arm. Diagnostic and spin keys were explicitly unset before applying the intended override. No model build, device-code change, affinity adjustment or power-setting change was needed.

Source and frozen CPU disassembly show the environment override populating the same pool member as the default. The worker converts microseconds to nanoseconds and checks the limit every 1,024 pause iterations. This proves the configured consumer path, not the number of runtime spin/sleep transitions. Scheduling and which worker claims work can still change; identical binary and available counters alone are not a proof of constant work or universal numerical equivalence.

## Completed model screen

The diagnostic-plus-ABBA schedule ran **2026-10-10 11:01:16.263192–11:13:57.855248 UTC**, exiting zero with cleanup complete. PP and TG rates below are arithmetic means of the two corresponding fresh-process arm rates; gains are candidate/baseline minus one. D0 is not included.

| Metric | Default 20,000 us, tokens/s | Candidate 100 us, tokens/s | Mean gain | A1/B1 gain | A2/B2 gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| PP | 646.923151815 | 647.042405640 | +0.018434% | -0.025856% | +0.062723% |
| TG | 53.870924103 | 52.747423078 | -2.085543% | -2.309717% | -1.861248% |

PP was effectively flat in this descriptive screen and its first pair was negative; TG regressed in both pairs. This result does not establish statistical significance or broad workload generality, but is sufficient to reject this setting under the frozen rule below.

All five complete 1,024-token output-ID arrays matched the historical reference exactly. All four clean performance arms matched available work counters, suffix counters, configured topology and READY affinity. Five optional counters remain unavailable/null: lookup-chain accepted/offered, native-suffix accepted/offered and decode windows. Available equality is not exhaustive proof of constant work. Configured affinity and observed allowed masks do not continuously attest active CPU placement.

## Fixed performance gate

The predeclared descriptive gate required either PP or TG mean rate improvement of at least 1%, both forward/reverse pairs positive for that metric, and no mean or either-pair regression in the other metric. All available work and suffix counters had to match. A weak or negative final result parks the setting without tuning or a rerun. This single ABBA is not a statistical-significance test.

D0 retained default spin and enabled DECODE_TIMING/SPLIT_TIMING plus CPU observation. It is excluded from all performance averages and pairs. A1/B1/B2/A2 had no CPU polling or decode/split/profiler flags. Each performance arm is a fresh process; paired results are A1 versus B1 and A2 versus B2.

## Descriptive baseline-only CPU diagnostic

D0 sampled only the owned process and its threads, starting at READY, at nominal five-second intervals and READY/first-token/DONE boundaries. CPU percent uses CPU ticks divided by SC_CLK_TCK and elapsed time, expressed relative to one logical CPU. Process and thread values are overlapping views and must not be added. Sampling has overhead, does not cover startup, and the first-token boundary includes output transport latency.

The independently recomputed D0 sample contains 24 observations and 28–31 threads. Before the first token, 18 included intervals span 101.500257 s and account for 165.68 CPU-seconds: **1.632311 logical-CPU equivalents** (163.231114% of one logical CPU). After the first token, four intervals span 18.872661 s and account for 305.29 CPU-seconds: **16.176309 logical-CPU equivalents** (1,617.630879%). One interval crossing a phase boundary is excluded. These are weighted interval aggregates; the phase labels approximate prefill and decode.

Observer reads took 0.348982 s, about 0.289870% of the sampled span; this is observed read overhead, not an estimate of all perturbation. There were no unavailable read entries. Positive recorded runqueue waiting occurred in 117 thread intervals, establishing some recorded scheduler waiting. It does not establish that contention caused the measured ABBA regression. No CPU observation was performed under the candidate setting, and no direct sleep, spin-transition or wakeup-latency count was collected.

High CPU use is not evidence that the sampled CPU time performed useful model work; it can include spinning. Context switches are not direct wakeup latency. Zero scheduler counters do not prove zero scheduling delay. D0 uses only the default interval, so it cannot establish the causal CPU-use change from 100 us or explain a performance regression by itself.

## Evidence and limits

The independent audit hashed 58 raw files and checked 229 admission events. Maximum sampled GPU temperature was 79 C, within the reviewed runtime guards; high power mode and the 190 W cap were unchanged. Admission and telemetry are sampled evidence.

[metrics.json](metrics.json) preserves numerical performance, the shared full 1,024-token ID array verified for all five arms, available-counter comparisons, optional-field availability and diagnostic aggregate evidence. Raw receipt archive: 128,985 bytes, SHA-256 fa23e9d1c07a80d6d7b158917d8ba4564e24660902ef8dce38f1319e3c7b7b53. Independent actual-audit SHA-256: 72a64994bb05337435005721047e5ecfb693ee55534de5567827d51c1a7ae49b. Hashes identify private retained evidence; they are not a public standalone reproduction package. Raw logs, host paths, credentials, model payloads and private process details are excluded. Only this report, its metrics and the archive index are proposed for publication. Runtime code, existing PR bodies and the stable deployment remain unchanged.
