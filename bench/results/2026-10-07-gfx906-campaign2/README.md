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

- CORRECTION (09:22 UTC): the earlier helper no-op conclusion was wrong. STRATA_PREFILL_MMQ=OFF in CMakeCache is the ordinary HIP option; gfx906 enables the CUDA-compatible branch, which compiles MMQ. Actual prefill target flags include STRATA_PREFILL_MMQ=1. The timing labels dequant/gemm are also used for MMQ gather/products and cannot identify the backend. Helper eligibility and benefit still require a live test; the prepared helper benchmark has not run.
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

## Mode16 at 64K

ABBA, 2048 outputs each, fixed placement/greedy, original seven flags in both arms.
Mode15 TG50.22217 -> mode16 TG50.57539 (+0.70331%).
A range50.1979-50.2464, B50.4594-50.6919: both B runs beat both A runs in this series.
All2048 IDs identical in all four runs. Accepted/offered counts1375/1691 match.
PP597.7-598.5 is effectively unchanged. Two repetitions per arm are not a universal guarantee.
No production promotion yet; Russian/longer-output validation remains pending.

## Idle-stage helper: engaged, default share not selected

Eight processes, ABBA at1536 and3072 input tokens,512 outputs each.
STRATA_PREFILL_HELP alone changes; seven selected settings and instrumentation remain equal.
The peer GPU really ran (streamed-expert counts and its phase timings were logged).
PP at1536:269.755->270.033 (+0.103%, overlapping variability).
PP at3072:325.579->311.450 (-4.340%); both candidate runs slower than both controls.
All512 output IDs match within each workload. Default helper share is not promoted.
This excludes this setting on these two fixtures, not every possible share or prompt.
The earlier absent-MMQ diagnosis is retracted above; the negative result here is measured.
