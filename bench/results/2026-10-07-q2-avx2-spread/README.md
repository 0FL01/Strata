# Exact AVX2 Q2 unpack screening

Xeon E5-2698B v3, one pinned CPU core, no concurrent inference.
Candidate widens eight packed bytes to32-bit lanes and spreads their bits.
Floating-point FMAs, correction and reduction are the original row implementation.
The VNNI route remains unchanged. Default off: STRATA_Q2_AVX2_SPREAD=1.

16,464 independent checks passed: every packed byte/value position through one-hot
rows, then random rows with1..8 tokens, zero/1/3/10/40 blocks, padded strides and
nonzero row ranges. Existing iq_avx2_parity passes with opt-in off and on.

Raw candidate microbench: ABBA timing on hot weights and a256-copy112.5MiB ring.
Rows640/blocks40 and rows2560/blocks10 match gate/up and down geometry.
One to three tokens improve about8-16% on the streaming cases. Four-token
groups regress up to4.36%; eight tokens inherit that path. This raw all-width
version is not selected. Next step: retain the old four-token kernel and use
bit spreading for the1..3-token remainder. No full-model gain claimed yet.

## Selected-width refinement

The new path retains the original four-token kernel, using spread only for
one-to-three-token tails. Widths divisible by four dispatch directly to the
original routine. VNNI and non-model block sizes remain unchanged.

All16,464 exact checks and existing parity tests pass again.32timing cases:
hot median1.07385x; streaming median1.07493x. Streaming T1..3 gains7.94-22.55%;
T5..7 gains3.07-9.33%. The unchanged T4/T8 route still has timing noise:
worst observed ratio0.98234x. Do not describe every measurement as faster.

These are single-core component timings, not model TG improvements.
Full-model fixed-placement4K/64K ABBA2048-output screen completed.
See selected-widths.json; raw all-width prototype is retained as a dead end.

## Full-model ABBA screen

Same candidate binary, STRATA_Q2_AVX2_SPREAD=0/1, all seven production flags,
mode15, no HC-SGEMM, unchanged placement, greedy sampling, prompt cache disabled.
Engine SHA256 ac6c7e8df0819eadf38fd00dc2dbd7ac6a85b15c81bc17fcec815c502cb9ffc3.
Two fresh processes per arm per context,2048 outputs each.

- 4K baseline TG52.48550/52.27677, candidate52.85025/53.05576.
  Pooled52.380928 ->52.952804 tok/s (+1.09176%).
- 64K baseline TG49.93161/50.11133, candidate50.66347/50.16952.
  Pooled50.021310 ->50.415286 tok/s (+0.78762%).
- All2048 output IDs match across four runs at each context. No reuse.
- Every candidate TG exceeds both corresponding baseline runs, but this is
  a small screening series, not an estimate with a robust confidence interval.
- PP4K345.44/348.66 versus347.86/341.91;64K597.33/598.46 versus599.58/596.14.
  No PP gain is claimed. Longer/different prompts and combined-path tests remain.
- Production baseline binary was restored before the series and service health
  restored afterward. Candidate is opt-in, not promoted.

Curated individual timings and output hashes:model.json.
