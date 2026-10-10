# Peer-prefill CPU placement: baseline diagnosis and controlled screen

**NO_QUALIFICATION: final C2 work-counter gate failed.** All seven engine arms completed and all 1,024 output IDs matched history, but frozen-control C2 performed different available decode work. The runner exited one and its failure remains preserved. Descriptive PP differences were **+2.086100% versus candidate OFF / +2.093669% versus frozen c183**; these are not an end-to-end qualification. Independently, candidate ON/OFF TG was **-0.009673%** with a negative first pair, failing the strict other-metric gate even without the work mismatch. No promotion, deployment or tuned placement rerun follows.

## Baseline CPU0 role diagnosis

One instrumented diagnostic used the frozen 65,536-token prompt and 1,024 greedy output tokens, seed 12345, residency 19,078 (9,900 + 9,178), adapt-every 0 and unchanged model/device work. Role tracing plus existing host-side timing was enabled; GPU profiling was off. The trace represents 65,535 batched prefill tokens: fifteen 4,096-token chunks and one 4,095-token chunk. The final prompt token is handled separately.

The independent actual audit verified exactly **81 scopes / 162 records** and CPU0-only affinity at every role entry/exit. Main stage thread CPU time was **58.378958351 s**; the peer dispatcher wrapper accumulated **41.489474825 s** and its nested peer-stage scopes **41.489167822 s**. Wrapper and nested stage measure overlapping work and must not be added. Issuer/PLE thread CPU time was much smaller. The non-nested role-thread total was **100.802952958 CPU-s** over a **101.095714202-s complete pipeline span**.

The main scope alone lasted 95.830176267 s; final peer completion occurred 5.265529087 s after main exit. Main-scope duration is therefore not total prefill duration. The role-thread total also excludes uninstrumented workers and is not whole-process CPU consumption.

Five-second observation produced 24 samples, mapping 65 scopes and leaving 16 unmapped. Only 15 fully contained main-stage intervals support the cited sampled scheduler totals: 52.175075053 CPU-runtime seconds and 36.529471327 recorded runqueue-wait seconds over 88.704847267 elapsed seconds. These intervals establish observed waiting while runnable. Unmapped/short-lived roles are unavailable, not idle or zero-wait. CPU/wait intervals and nested scopes must not be summed into removable wall time. Observer reads took 0.344202500 s; that is measured read time, not all instrumentation overhead.

Full output IDs and all available historical work counters matched. Diagnostic prompt/decode times were 101,292.5 / 19,028.3 ms, recorded as observations only, not a performance comparison. Maximum sampled GPU temperature was 77 C; cleanup passed. The audit is diagnostic evidence, not qualification of a scheduling change.

## Preserved first-attempt packaging failure

Diagnostic v1 failed before engine execution because its archived binary copy had mode 0644 and was not executable. The original failure, marker and receipts remain preserved. Diagnostic v2 used an already existing linker output with mode 0755 and the same independently reviewed binary hash; no chmod, rebuild, source or arithmetic change was needed. The corrected runner checks executable access, owner/group and unsafe write permissions before its lock/attempt marker and again before launch. This technical launch repair is distinct from a performance rerun.

## Narrow CPU1 candidate and compile evidence

The candidate changes only a bounded host peer-stage placement scope. With runtime STRATA_PREFILL_PEER_CPU1 exactly 1, the eligible primary-device0-to-terminal-device1 call requires CPU0-only entry affinity, saves the complete mask, pins to CPU1, verifies placement, executes the same peer work once, restores the original mask and verifies restoration. Failure paths reject; exceptions restore via scope cleanup and propagate. With placement unset, the existing call runs without new placement queries or changes.

The primary/main issuer and PLE roles remain CPU0. Peer-stage issuer children inherit CPU1. The runner requires CPU0/CPU1 online and allowed, on distinct physical cores; observed sibling sets are (0,16) and (1,17). Pool-worker placement, cpusets, OS scheduling policy, power, frequency and security settings are outside this change. The code is deliberately bounded to the checked Linux/two-device configuration rather than a general topology policy.

Independent actual build audit passed: macro-OFF exactly reproduced frozen c183, candidate and OFF binaries were executable, all **55 device modules were identical**, 70 retained artifacts were verified and cleanup passed. Candidate SHA-256 is 79ba570f5eead6095e5f1033c461b0653d1cd177440bb08ffa30b38902ad53c0. Exact GPU images do not prove host scheduling correctness; runtime placement, restoration, outputs and counters still require their own checks.

## Fixed diagnostic and clean performance method

The candidate schedule is one placement-validation D0, then exactly **C1, A1, B1, B2, A2, C2** in fresh processes:

- C: frozen c183 binary
- A: candidate macro-enabled binary, runtime placement unset
- B: same candidate binary, STRATA_PREFILL_PEER_CPU1=1

D0 includes role and CPU observation and is excluded from performance. All six clean arms explicitly clear diagnostic/profiling and spin overrides, retaining the same prompt, output length, native arguments, residency and workload settings. READY/DONE bounded CPU/MEM-mask inventories are collected identically; native phase timing ends before DONE inventory capture. Configured masks do not continuously attest active CPU placement.

D0 must verify all 81 paired role scopes and expected masks: main/primary issuer/PLE endpoints CPU0, nested peer stage/issuer endpoints CPU1, and outer peer-dispatch endpoints CPU0 after restoration. Transition samples may observe either CPU during pin/restore; missing short-lived samples remain unavailable. Whole pipeline timing includes final peer completion beyond the main scope.

The frozen gate requires at least **1% PP or TG mean-rate gain in both B-versus-A and B-versus-C**, both forward/reverse pairs positive, and no mean or either-pair regression in the other metric in either comparison. A-versus-C overhead is reported separately. PP is the primary hypothesis. Full generated IDs and all available work counters must match historical evidence and one another; optional unavailable counters remain null. One fixed target and one fixed screen provide descriptive evidence, not statistical significance or universal exactness.

## Actual fixed-screen failure

The seven engine processes completed on 2026-10-10, each with native exit zero and all 1,024 IDs exactly matching the historical reference. The enclosing runner exited **one** at the final C2 historical-work check. C2 is the frozen c183 control, not the placement candidate. Its drift is retained exactly:

| Counter | Historical / D0,C1,A1,B1,B2,A2 | Frozen C2 |
| --- | ---: | ---: |
| Offered | 872 | 873 |
| Lookups | 600,000 | 600,480 |
| Cache hits | 582,049 | 582,512 |
| Suffix offered | 16 | 17 |
| Accepted | 648 | 648 |
| Suffix accepted / windows | 9 / 5 | 9 / 5 |

Five optional counters remain unavailable: lookup-chain accepted/offered, native-suffix accepted/offered and decode windows. The separate available suffix-summary counters above are present; unavailable optional fields are not zero. No arm was excluded, repaired or rerun and no raw receipt was rewritten. Matching tokens do not override the frozen available-work gate.

### Descriptive clean-arm rates, not qualification

Means are arithmetic means of two fresh-process rates per mode. D0 is excluded. Gains use candidate/control minus one; the original forward/reverse pairing is retained.

| Mode | PP tokens/s | TG tokens/s |
| --- | ---: | ---: |
| C: frozen | 635.984985095 | 53.808506723 |
| A: candidate OFF | 636.032141281 | 53.863979062 |
| B: candidate ON | 649.300407238 | 53.858768725 |

| Comparison | PP mean gain | PP forward / reverse | TG mean gain | TG forward / reverse |
| --- | ---: | ---: | ---: | ---: |
| B versus A | +2.086100% | +2.425788% / +1.748705% | -0.009673% | -0.103009% / +0.083693% |
| B versus C | +2.093669% | +1.712595% / +2.477555% | +0.093409% | +0.046775% / +0.140015% |
| A versus C overhead | +0.007415% | -0.696302% / +0.716324% | +0.103092% | +0.149938% / +0.056275% |

PP exceeds the numerical 1% criterion in both comparisons, but the combined frozen gate still fails. B-versus-A TG has a negative mean and first pair (-0.103009%), independently violating the no-regression condition. The small magnitude is not a statistical-significance claim. Two arms per mode and C2 work drift prevent reporting these figures as a qualified end-to-end improvement. A-versus-C overhead is preserved separately rather than assumed zero.

The exact c183 executable contains wall-time-dependent draft-policy observation and selection, corroborating a mechanism by which decode work can vary despite matching token IDs. The precise C2 choice was not logged, so attributing this specific drift to that mechanism remains a hypothesis. PP timing is captured before decode; later suffix decisions cannot retroactively alter the recorded PP interval. This chronology does not relax the predeclared combined workload or TG gate.

## Actual CPU1 placement and unpaired diagnostic comparison

The new D0 independently passed all 81 paired scopes / 162 records: main/primary issuer/PLE endpoints stayed CPU0, nested peer stage/issuer endpoints were CPU1, and outer peer-dispatch restoration returned to CPU0. Within each of the seven arms, all 28 persistent thread identities and their READY/DONE affinity inventories matched. Endpoints and sparse observations do not prove continuous scheduling residency.

The two instrumented diagnostics, one earlier CPU0 baseline and one new CPU1 run, show:

| Diagnostic observation | Earlier CPU0 | New CPU1 |
| --- | ---: | ---: |
| Main contained sampled runtime, s | 52.175075053 | 86.752370849 |
| Main contained sampled runqueue wait, s | 36.529471327 | 0.632265846 |
| Included main sample intervals | 15 | 15 |
| Non-nested labelled role CPU time, s | 100.802952958 | 170.926599974 |
| Complete role pipeline span, s | 101.095714202 | 99.684077694 |

These are **unpaired, separately instrumented observations**, not a paired speed comparison. Much less observed runnable waiting coincides with substantially more labelled CPU runtime; the additional runtime can include spinning or waiting rather than useful computation. Nested wrapper/peer scopes still must not be added. Neither scheduler waiting nor thread CPU time identifies removable critical-path time or causally explains the clean-arm rates. The CPU1 D0 has 24 observations, 65 mapped scopes, 16 unmapped scopes and 0.345872284 s observed read overhead.

Independent actual audit passed as an audit of a **failed screen**. It verified 79 regular raw files, full IDs, runtime bindings, diagnostics and cleanup. The peak captured sensor was **82 C** within the reviewed runtime limits; final maximum sensor was **52 C**. Those are different observations, and the final reading is not the peak. No further placement variants or rerun are part of this result.

## Evidence and publication scope

[metrics.json](metrics.json) records the verified baseline diagnosis, build evidence, all seven arm rates/counters, descriptive comparisons, diagnostic aggregates, unchanged gates and audit seals. Raw archive: 188,002 bytes, SHA-256 e3ed8a3464a6b8ab31583d5cdc5407b1c44970cdd15ce5bee154ddf8c2afa815. Independent actual-audit SHA-256: 4e1a763a650d2bad5e774d237f7e64bdaf9d55ba04806080ab0ee085b1fdf25d. Audit success does not mean qualification success. Only this report, its metrics and the archive index are proposed. Private host paths, model payloads, credentials, raw logs and raw process identities are excluded. Previous experiment reports, runtime code and PR bodies remain unchanged.
