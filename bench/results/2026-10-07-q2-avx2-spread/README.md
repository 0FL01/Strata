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
Full-model fixed-placement4K/64K ABBA2048-output qualification is running.
See selected-widths.json; raw all-width prototype is retained as a dead end.
