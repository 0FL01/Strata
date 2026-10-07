# Selective HC FP16 numerical experiment

Baseline is the separately qualified exact stack b6731bf; preserve its binary.
Hotspot: BF16 HC down/up GEMMs in prompt processing. Conversion-inclusive
component pair is about7.76ms versus10.96ms for the earlier arena SGEMM path.
Expected incremental warm4K PP opportunity is roughly3%, not a measured model
gain; native BF16 is slower still. Cheapest falsifier is an audited real4K read
followed by cold/warm A/B/B/A with route proof.

This is not an exact-input change: among635699200 actual BF16 HC weight values,
63197 change on FP16 conversion and400 become zero; no source nonfinite or
overflow. Actual selected weights with synthetic normal BF16 inputs have
full-output relativeL2 differences up to5.88e-8 against native BF16; model
activations and quality still require validation.

Opt-in STRATA_GFX906_HC_F16=1 only for T4095/4096 and the two measured shapes.
It borrows idle phase storage, preserves original xn16 for inject, retains FP32
output/compute, and excludes peer-expert/helper, FP16-I/O and BF16X2 scopes.
Unsupported geometry, stride, beta, capacity or aliasing keeps native BF16.
No matrix allocation, scaling or saturation is added.

STRATA_HC_F16_AUDIT=1 counts actual input conversion changes/ranges and scans
outputs for nonfinite values. It synchronizes and is excluded from timing.
STRATA_HC_F16_TRACE records attempted/taken calls. Neither is model quality proof.
The patch is experimental and unbuilt at this checkpoint.

Review fixes: audit maximum now reduces per block rather than serializing every value; ldy is bounded by the BLAS int interface. Ordinary layer-split stages still qualify; layer-pipeline execution is not independently qualified. Explicit beta/stride/capacity/alias refusal tests remain pending.

## Actual route audit and whole-model screen

Fresh build of f9065d1 plus the four existing deployment patches passed the
isolated route probe on both gfx906 cards. Eligible calls all took the new path;
unsupported shapes retained native BF16. The disabled prototype reproduces the
qualified exact engine's1024 output IDs.

An actual uncached4K request exercised192 calls (108+84 across the two stages):
maximum absolute X71.5 and W8.5625, no input overflow/nonfinite and no nonfinite
FP32 output. Across this call stream,1,268,975 X values changed on conversion
and384,124 became zero; W counts62385 and396 respectively. Those are repeated
operand-conversion events, not a unique model-weight census.

Enabled generation first differs after168 matching tokens. This establishes
numerical divergence; it is not itself a quality verdict. No exactness claim.

Four fresh processes A/B/B/A, four uncached4K requests per process,256 outputs
each; all best-known exact settings and MTP16K/HIGH fixed in both arms.
First requests: PP347.95905 ->378.51974 (+8.78284%).
Subsequent requests: PP358.93983 ->391.50653 (+9.07302%).
Prompt reuse was0 and every request read4096 tokens. Audit/synchronizations
were disabled for timing; route summaries remained enabled. Do not infer a TG
speedup from numerically divergent generated work. GPU profiles restored AUTO.

Performance executable:
8152d8ba908b29c92476e5c79ea089d9810f2a887e670eaf141b7d7a30b5a6a9
See prefill-screen.json for observations and numerical-scope limits.

A separate diagnostic-only commit13e26a9 ports the existing first-logits dump
to serial serve with explicit final-stage device selection and checked writes.
It has no GPU allocation and is not used in the performance numbers above.
Code/Russian A/A/B first-distribution and residual checks are pending.
The exact qualified stack remains separate and unchanged.

Diagnostic follow-up: STRATA_HC_F16_ARENA_ONLY=1 performs the same arena conversions but falls through to unchanged native BF16 math. This isolates scratch-lifetime corruption from the numerical route. It is diagnostic only, not a performance option.

STRATA_HC_F16_SHADOW=1 runs the full FP16 route, samples64 outputs, then overwrites Y with the original native BF16 product and samples the same coordinates. Downstream state should match baseline if there is no scratch/library side effect. No extra GPU matrix buffer is allocated. Diagnostic only.
