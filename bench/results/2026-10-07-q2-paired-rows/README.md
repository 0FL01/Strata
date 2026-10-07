# Q2 paired-output-row hypothesis

Two output rows reuse each token's activation loads at NT1/2. Each output
retains the selected spread kernel's FMA, correction and horizontal-reduction
order. Other token widths use the selected spread implementation unchanged.
This is an explicit test entry point only, not wired into engine dispatch.

Controller nc-lab, x86_64, GCC14.2.0:
- Compile with -O3 -mavx2 -mfma -mf16c -DSTRATA_AVXVNNI=0 passed.
- Functional test:16,464checks,0failures. Exhaustive byte-position witnesses
  now exercise both paired rows with complementary codes; random tests include
  odd row tails, nonzero output ranges, padded strides, NT1..8 and0/1/3/10/40blocks.
- ASan+UBSan -O1:16,464checks,0failures; leak detection explicitly disabled.
- No controller performance result is claimed.

The reverse SSH outage initially prevented timing. After the host returned,
persisted receipts showed this test had not started, so one cheap MI50-host
component run was performed:16,464 parity checks,0failures. Streamed256-copy
down shapes improved kernel throughput9.01% atNT1 and4.73% atNT2, while
gate/up atNT1/2 regressed1.73%/.44%. The unchanged NT3 down path also varied
by-12.65%, so this single run is not a stable-performance qualification.

Parked under the campaign's Pareto rule: the exposed CPU tail is small and
the expected whole-model benefit is low; no engine integration or full-model
run is justified by this screen. No deployment. Raw single-run timings:
mi50-run0.log.

Reference for paired testing is the already-qualified selected-width spread
implementation. STRATA_Q2_TEST_PAIR=1 selects this comparison; do not set engine
STRATA_Q2_AVX2_SPREAD=1 while running the test's independent reference.
