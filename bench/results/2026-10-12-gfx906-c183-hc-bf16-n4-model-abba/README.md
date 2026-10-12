# gfx906 c183 HC injection N4: shadow and 64K model ABBA

**Mean PP throughput improves 2.776349%: 646.882607→664.842326 tokens/s.** Pair gains are **+2.770136% / +2.782561%**, passing the frozen ≥1%-mean/both-positive gate. Mean prompt elapsed time falls **101,310.50→98,573.75 ms**, saving **2,736.75 ms (2.701349%)**.

Four fresh-process runs use the same c183-derived binary in **OFF, ON, ON, OFF** order on one **65,536-token prompt / 1,024-output greedy fixture**. All four output trajectories and every available native-work counter match historical controls. Both ON arms retain candidate output for all **1,536 injections**, with shadow disabled and no fallback.

Mean TG is **53.899308→53.839527 tokens/s (−0.110912%)**. Its ratio **0.998890879** passes the frozen **0.99** practical tolerance; this is not proof of identical throughput. No retries or arm exclusions.

The preceding shadow screen compares **1,536 real-activation calls / 25,165,440 FP32 elements**, with zero bit mismatches, nonfinite outputs or errors. Shadow preserves reference output downstream and supplies per-call evidence; the separate ABBA validates the candidate-output trajectory. Timed arms do not compare internal tensors.

Scope is the pinned **c183/gfx906/rocBLAS GSU3, BF16 N4/K10240/T4095–4096** opt-in path; global prompt-F16 stays OFF. [Prior component results](../2026-10-12-gfx906-c183-hc-bf16-n4/README.md) remain intact. Independent shadow/ABBA audits pass **306/585 checks**; cleanup passes, final maxima **55/53 C**, API stopped. [Metrics](metrics.json) retain exact values and hashes. No universal exactness, broad-quality or default-promotion claim; 4K/200K qualification is outside this report.
