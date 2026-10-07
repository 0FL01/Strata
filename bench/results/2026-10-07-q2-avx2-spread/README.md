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
