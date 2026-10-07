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
