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

## Combined exact Q2 candidate

Mode16 GPU gate/up+down integer unpack with selected-width CPU AVX2 spread,
against mode15/CPU spread off. Both arms retain the seven qualified production
settings, MMVF tile4 and HC-up exact off. Same binary and pinned baseline epoch.
Native text, fixed placement, greedy, no reuse,64Kprompt,4096outputs, ABBA
(two fresh processes per arm per workload):

- Code TG49.89834 ->50.63188 tok/s (+1.47007%).
- Russian TG40.85818 ->41.41685 tok/s (+1.36733%).
- Every4096output ID matches across each workload's four runs. The first2048
  also match all prior controlled production-qualification runs on the original
  engine binary. Both candidate TG runs exceed both baselines in each workload.
- No PP gain: code598.31678 ->595.22528; Russian597.91693 ->595.54252 tok/s.
  The changes target decode; small negative PP observations are retained.
- No new weight/KV quantization, no Russian vocabulary change, no clock or power
  modification. No arbitrary-prompt quality or universal percentage claim.

Results finished before a reverse-SSH outage and were recovered after host
reboot; no completed model case was rerun. Initial driver attempt failed on a
label NameError before anygeneration, was fixed, and its logs retained.
Production restore receipt14:35:32UTC is historical, not current server health.

Curated raw phase times, output hashes, counters and binarySHA:exact-combined.json.
Candidate is preserved, not yet deployed as a new production build.

## Configuration qualification on the exact Q2 candidate

Both arms use mode16 and selected CPU spread, retaining the seven previously
qualified settings. A uses AUTO and MTP window32768; B uses normal amdgpu HIGH
and MTP window16384. Main context204800 and resident INT8 KV32768 are unchanged.
B reserves623MiB on the later GPU instead of600; both arms explicitly retain
9900 primary +9178 secondary expert slots. No power limit or voltage increase.

Fresh processes, fixed placement, greedy, no prompt reuse:
- 4K code,1024 outputs,A/B:54.07746 ->55.75156 TG (+3.09574%).
- 64K code,2048 outputs,ABBA:50.99443 ->53.02293 TG (+3.97789%).
- 64K Russian,2048 outputs,ABBA:48.73220 ->50.61802 TG (+3.86976%).
- All output IDs match within each workload. Draft accepted/offered counts
  differ with the shorter MTP window. Equal output does not establish identical
  internal work or quality on arbitrary prompts.
- No material PP gain. These gains are additional to the exact Q2 comparison,
  but percentages from different output lengths/epochs must not be simply added.

Preliminary separate64K/512-output ABBA screens found MTP16K +1.53876% TG
and normal HIGH +2.19255% TG. They motivated the longer combined test, not
independent deployment promises. HIGH is a machine-specific runtime setting,
not a source-code optimization. All tests restore AUTO afterward.
Production has not been promoted. Actual200K capacity and API qualification
remain separate gates. Curated durations/counters/output hashes and binary SHA
are in config-qualification.json. Hardware sensor logs remain local.

Qualification caveat for the earlier exact-combined Russian runs: accepted/
offered draft counters vary slightly even between baseline repetitions.
Output equality is verified; identical speculative work is not claimed.

### Actual 200K capacity check

The candidate processed200000 fresh prompt tokens and generated256 output tokens
with main capacity204800, INT8 resident32768 and unchanged19078 expert slots.
PP573.88365 tok/s, TG42.57938 tok/s; exit0, AUTO restored. This synthetic capacity
check is not a controlled200K speed comparison and is not a quality evaluation.
API/tool/vision qualification and clean-build promotion remain pending.
See config-capacity-200k.json.
