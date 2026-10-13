# REG2 + FIT17: bounded eight-arm model qualification

**PASS for the pinned 64K/1024 profile.** Fresh B0 baseline versus S2 with REG=2/FIT17=1, on two gfx906 owners at `a0116b2`; aux CPUs and prompt F16 stayed off. Eight fresh engines ran fixed ABBA then BAAB, with no exclusions.

| Block | Mean PP change | Mean TG change | Frozen gates |
|---|---:|---:|---|
| ABBA | −0.012001% | +1.087012% | PASS |
| BAAB | +0.753949% | +2.468158% | PASS |

Each block required TG gain ≥1%, both TG pairs positive, and PP mean ratio ≥0.995. That PP tolerance permits 0.5% loss; ABBA did lose PP. The four TG pair gains were +2.052437%, +0.122415%, +2.534631%, +2.401787%.

Pooled arithmetic-mean PP was 581.894568→584.045236 tokens/s (+0.369597%); TG was 48.313073→49.171839 (+1.777504%). Mean request wall time fell 774.713 ms, but **load plus request rose 6.550 ms**. [Metrics](metrics.json) retain every arm, block and pair, including load times.

All eight full 1024-token outputs and recorded work matched. Capacity/census checks and cleanup passed; final maximum 52°C, API stopped. Earlier model correctness pairs also matched: the 4K/32 pair retained a **7.4 ms decode loss (TG −1.024931%)**; the 64K/1024 single pair gained 2.247500% TG. Those timings remain descriptive.

This qualifies the combined pinned configuration, without isolating REG2/FIT17 contributions. Actual device-body selection was not independently observed. There is no default promotion, universal exactness or statistical zero-loss claim. [Build/component evidence](../2026-10-13-gfx906-a0116b2-selector-components/README.md) preserves the harness refusal and scratch/spill caveats. Attachments concern existing [#1535](https://github.com/Niko1221/Strata/pull/1535) and [#1743](https://github.com/Niko1221/Strata/pull/1743).
