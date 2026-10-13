# Q2 grouped-expert: bounded eight-arm model qualification

**PASS for the pinned 64K/1024 profile.** Fresh B0 mode7 versus Q1 mode15 ran fixed ABBA then BAAB on two gfx906 owners at `a0116b2`. Aux CPUs were off; N4/selector opt-ins were absent. All eight arms were retained.

| Block | Mean TG change | Mean PP change | Frozen gates |
|---|---:|---:|---|
| ABBA | +2.983887% | −0.003910% | PASS |
| BAAB | +3.120509% | +0.048364% | PASS |

Each block required TG gain ≥1%, both TG pairs positive, and PP mean ratio ≥0.995. **PP permits 0.5% loss**; ABBA did lose PP. All four TG pairs improved (+3.000524%, +2.967260%, +2.731221%, +3.512785%).

Pooled arithmetic-mean TG was 48.193895→49.664823 tokens/s (+3.052105%); PP was 583.770438→583.900233 (+0.022234%). Mean request time fell 643.898 ms; load plus request fell 595.536 ms. **The first pair's load plus request increased 500.317 ms.** Earlier exact 4K/32 and 64K/1024 single pairs also retained load-inclusive losses of 196.124/384.985 ms.

All full outputs, recorded work and capacities matched; cleanup passed, final maximum 51°C, API stopped. The actual audit passed 1,154 checks plus its startup/lifecycle supplement. [Metrics](metrics.json) retain every native/load/request timing, printed MTP span and startup residual. MTP includes reads, allocation/copy/synchronization and setup; the residual is unlocalized. Load-inclusive sums omit teardown/cooldown and are outside the frozen gates.

[Component/static/census evidence](../2026-10-13-gfx906-a0116b2-q2-components/README.md) remains separate. Executed device bodies were not independently observed; the other 151 changed baseline bodies remain outside equivalence proof. This establishes no general zero-loss guarantee, default promotion or combined selector/Q2 qualification. Existing PR #1187 is unchanged.
