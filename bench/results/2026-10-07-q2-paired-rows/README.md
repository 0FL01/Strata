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

MI50-host component timing was queued behind the combined model comparison.
The reverse SSH listener on the relay disappeared around14:34UTC on2026-10-07.
Controller-side SSH jobs ended255; execution/receipt state on MI50 is unknown.
Inspect persisted receipts and live processes when access returns before any
rerun. No MI50 timing, full-model gain or deployment is claimed for this change.

Reference for paired testing is the already-qualified selected-width spread
implementation. STRATA_Q2_TEST_PAIR=1 selects this comparison; do not set engine
STRATA_Q2_AVX2_SPREAD=1 while running the test's independent reference.
