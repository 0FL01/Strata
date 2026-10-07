# Second gfx906 Hybrid campaign

Baseline: deployed 82f4473, runtime cc7eeb6, seven previously qualified settings.
Two gfx906 16 GiB cards, Xeon E5-2698B v3, 128 GB RAM.
Model and 204800 capacity unchanged. Work began 2026-10-07 08:20 UTC.

## Upstream overlap review

168 open PRs inspected at 08:22 UTC. Existing Q2 work is #1187; exact-path tests are now #1320.
- #1316: stale lookup-cost re-probe; candidate for independent adoption test, do not duplicate implementation.
- #1296: WY recurrence already loses on author's gfx1100; no matrix cores here. Low priority.
- #1237: pinned staging applies when the full resident arena is unavailable; ours fits. No expected steady-state benefit.
- #1282: CPU prefill share currently single GPU. Not a drop-in layer-split optimization.
- #1247: exposes existing prefill-helper settings as CLI; no new compute implementation.

## Screened paths

- Idle-stage prefill helper: current gfx906 binary has MMQ disabled. set_stage_helper exits when mmq_plan().any is false. Enabling STRATA_PREFILL_HELP alone cannot activate it. Prepared helper benchmark was not launched; avoid benchmarking a proven no-op. Supporting this route would require a separate backend implementation.
- Prior campaign's pipeline output divergence, shared-stream loss and planner noise remain documented in ../2026-10-07-gfx906-campaign; no blind repeats.

## Pending

Profile current paths, test transposed reductions with independent parity checks, test Q2 gate/up bit spreading, and evaluate #1316 separately. No new speed claim yet.

## Initial Q2 gate/up component screen

Mode16 changes only gate/up integer unpacking from mode15; its down remains identical.
Real model layers 0/23/47, both GPUs, groups 1/8/32, tokens per group 1/2/4/8: 72 cases.
Every gate/up/SwiGLU value, active Q8 byte and expert output matched bitwise.
Gate/up speedup min/median/max: 1.0246/1.0855/1.3069x.
Whole-expert speedup: 1.0158/1.0378/1.1540x. Rates derived from rounded microsecond output;
three interleaved timing rounds use the minimum, not a confidence interval.
This is a component screen, not an end-to-end throughput or model quality claim.
Full-model alternating screen is pending.

STRATA_TSUM=1 with the current rows/fusion/mode15 profile passed mmvf_rows_parity,
gr_multi_parity and native_grouped_parity on both GPUs (six invocations).
The rows test has 432 cases / 1660200 checked values per GPU; all zero mismatch.

Profiling baseline: code4K, 1024 outputs, instrumentation on.
Expert GEMMs account for about30% of summed per-stage GPU prompt timelines;
hyper-connection read about22%. Timelines overlap and are not end-to-end fractions.
At64K: 376 decode windows, average3.30 verified /2.72 emitted tokens per window;
57.57ms/window, verification49.94ms, commit1.49ms, draft6.13ms.
Instrumented speed is not an optimization A/B result.

## Full-model 4K screen

Fresh processes A-T-Q-Q-T-A, fixed placement, greedy, 2048 outputs each.
A is deployed mode15 with seven flags; Q changes mode16 only; T adds TSUM to A.
Aggregate TG: A52.8522, Q53.1630 (+0.588%), T52.9969 (+0.274%).
All output IDs identical. Per-arm rate ranges overlap; neither is a stable-gain claim.
One Q repetition changed offered/accepted draft counts slightly, with the same output.
TSUM is not selected from this screen. Mode16 proceeds to independent64K ABBA.
See screen-4k.json for durations, rates, counters and output hashes.

## Other work prepared

Upstream #1316 was cherry-picked independently with original authorship; its expanded CPU
draft_policy_test passes with -O2 -Wall -Wextra -Werror. GPU evaluation pending.
Upstream #1123 is staged independently for gfx906 SGEMM microbenchmarks.
Exact widening preserves input values but changes summation order; this is not a
bitwise-equivalent route, and no model quality or speed claim is made before tests.
