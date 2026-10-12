# HC BF16 N4 decode diagnostic: slowdown not reproduced

**The prior slowdown did not recur in this one diagnostic pair.** Decode time is **19,006.0→18,971.4 ms**, a **34.6 ms reduction**; TG changes **+0.182380%**. This does **not** fix or explain the [earlier four negative TG pairs](../2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/README.md), replace them, or establish zero loss.

The same c183-derived binary runs one **64K/1,024-output OFF→ON pair**, with existing DECODE_TIMING enabled and VERIFY_PROFILE absent. The flag prints after the native decode interval; its clocks already run unconditionally. No new GPU events or timestamp instrumentation were added.

Both arms have **379 windows** and historical-exact output/work: accepted/offered **647/868**, cache hits/lookups **580,670/598,560**. ON takes all **1,536 candidate calls**, with global prompt-F16 and shadow OFF.

Printed phase estimates:
- Verify: **17,108.06→17,073.95 ms**, change **−34.11 ±3.79 ms**
- Commit/emit: **174.34→174.34 ms**; draft: **1,720.66→1,720.66 ms**, each change **0 ±3.79 ms**
- Unassigned residual: change **−0.49 ±11.47 ms**

These are **rounding bounds, not confidence intervals**. Nested counters mix primary-Verifier and shared-Drive scopes; they cannot be summed into owner-level GPU time. Residual time is not GPU-idle time.

Independent actual audit passed **324 checks**; cleanup passed at **53 C**, API stopped. [Metrics](metrics.json) retain phase semantics, uncertainty and hashes. The original unfavorable results remain unchanged and unexplained; no additional repeat or performance qualification is included.
