# Release-local strict HC: parked after synthetic timing

**Component correctness PASS; frozen hypothetical timing gate FAIL.** This opt-in strict HC candidate is based on release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`. It uses guarded FP16 conversion with native fallback and borrowed scratch. The timing probe reused the same candidate engine and static archives without production changes. No model run, promotion or throughput gain follows.

## Full-output component checks

Both physical gfx906 devices passed **64 full-output comparisons** in total: four shapes × eight synthetic cases per device, with **24 fast-route calls / 40 fallbacks**. Full canaries, input immutability, output finiteness, rejected scratch checks and 32 cancellation witness rows passed. All eight signed-zero cases used fallback. Complete tensors were compared in memory by the reviewed, PID-hash-bound probe; full tensor bytes are not retained offline. This is empirical coverage, not universal GEMM equivalence; NaN/Inf rejection was source-reviewed only.

## Fixed GPU0 timing screen

For each of eight cells, one native reference preceded two warmups per arm and three ABBA quartets: **8 references, 32 warmup and 96 measured samples**, all fully checked. A is the same binary with strict mode ON and null scratch, so it includes rejection/counter overhead and is not production strict-OFF. B uses valid scratch; random case 0 must activate and tiny-W case 4 must fall back.

The monotonic host interval includes conversion, guard copy/synchronization, GEMM and final stream completion. Setup, resets, counter reads, transfer and validation are outside. Interleaved full validation affects synthetic cache/cadence. Values below are medians of three signed quartet differences, `(A1 + A2 - B1 - B2) / 2`; fallback penalties reverse that sign.

| T | N × K | Fast saving, ms | Tiny-W fallback penalty, ms |
| ---: | --- | ---: | ---: |
| 4095 | 320 × 10240 (down) | 6.417143 | 0.1095555 |
| 4095 | 10240 × 320 (up) | 3.2291755 | 0.0719300 |
| 4096 | 320 × 10240 (down) | 5.4850105 | 1.4664525 |
| 4096 | 10240 × 320 (up) | 3.2100945 | 0.1070035 |

All **12 fast quartets were positive**. The frozen rule takes `S = min(fast medians) = 3.2100945 ms` and `P = max(0, max(signed fallback medians)) = 1.4664525 ms`. Its historical, hypothetical mixture gives:

`528*S − 1200*P = −64.813104 ms`, below the strict `> +1036.092079 ms` gate corresponding to a 1% PP improvement over the historical reference.

The zero-net break-even fast fraction is **31.3575914%**, versus **30.5555556%** in that hypothetical mixture; break-even does not include the additional 1% threshold. All 24 signed paired deltas are preserved in [metrics](metrics.json), including all three 4096-down fallback penalties, **1.4664525 / 2.5666885 / 0.2932105 ms**, without exclusions. **GPU1 timing did not run**, as required by the fixed early-stop policy; both owners were required to advance.

## Preserved failure, repair and decision

V1 had a valid initial process binding but failed on a late process-environment `PermissionError`. The probe completion record and container CLI exit zero were present, but no contemporaneous process-state snapshot proves an exit race. V1 remains **invalid** and supplies no performance-selection values.

V2 changed only lifecycle handling and versioned runner names, retaining immutable process/container identity, the same probe/binary/order and the original gate. Exit-race recovery requires positive termination plus owned-container CLI exit zero; **that recovery branch was not used in V2**. Independent actual-raw audit, parser rerun and integer-nanosecond reduction passed; this audit pass is separate from the failed performance gate.

**PARK_INSUFFICIENT_HYPOTHETICAL_SIGNAL.** Current-model fast-route activation remains unknown. The result does not prove that every workload loses, nor a global workload bound. No model run, performance retry, threshold change, deployment or promotion occurred. Cleanup passed with API stopped, high mode / 190 W unchanged, and final maximum 45°C. Metrics retain numeric evidence and provenance hashes; raw logs, private paths, configuration contents and model payloads are excluded.
