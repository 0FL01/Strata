# gfx906 c183 HC injection: input-exact route rejected, probe incomplete

**All 96 finite ordinary cases fail original FP32-output byte parity despite accepted CPU/GPU operand guards.** Across **1,572,864 elements**, **1,519,845 differ (96.629143%)**: **15,723–15,972 of 16,384** per case, median **15,820.5**.

The fixed-scale candidate uses one deterministic BF16 activation fixture and **96 actual weight tensors**, shape **T=4096, N=4, K=10,240**, with activation/weight scales **512/4096**. It compares against the literal archived BF16 GEMM's FP32 output. Direct BF16 control matches exactly, as do two actual-subnormal one-hot cases. Exact operand representation did not preserve this candidate's ordinary GEMM outputs; a unique internal cause is not established. Mismatch frequency does not measure error magnitude or model-quality impact.

After **98 valid partial parity records**, the probe aborts with `CPU GPU exact guard`. Source order places the next case at the signed-zero adversary; no result for it was emitted. Operand/flag details were not retained, so the cause is unproven. **Exit 1; incomplete:** T4095, remaining adversaries, fallback completion, timing and the terminal done record were not reached.

The route is rejected without integration or a speed result. Independent audit validates the **partial evidence**, not diagnostic completion. Cleanup passed, final maximum **46 C**, API stopped. [Metrics and hashes](metrics.json) preserve the exact boundary.

Scope correction to the [earlier observer](../2026-10-12-gfx906-c183-pp-bf16-exposure/README.md): excluded HC down/up has a **partially taken guarded route**, not universal optimization. Combined takes/attempts were **531/1,728 primary** and **567/1,344 peer**; no down/up split or remaining-fallback exposure was measured.
