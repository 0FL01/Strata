# gfx906 c183 GEMM: output diagnosis and signed-FIRST4 rejection

**All four tested FP32-output alternatives match the entire synthetic fixture bit-for-bit, but lose all 32 timing pairs.** Candidate medians are **29.784–33.656 ms**, versus paired reference medians **15.058–15.188 ms**. No speed winner or integration follows; **55 returned solutions remain untested**.

The owner-0 fixture is one deterministic projection shape, **T=4096, N=2560, K=6144**, with identical already-FP16 inputs/weights and an FP32-output archived-Gemm reference. It contains **10,485,760 output values**.

Rounding that reference to FP16 and widening changes **10,483,999 values**. Actual FP16-output results differ from the rounded reference at **73,709 positions (0.702944%)**. All compared outputs are finite; this demonstrates loss beyond final storage rounding alone, without identifying a unique internal library cause. The numerical diagnosis repeats unchanged in V1/V2.

V1's positive-only filter selected **zero** of 59 negative signed solution identifiers, so it tested no alternatives. V2 preserves that result and uses a frozen signed-ascending **FIRST4** rule, with no replacements. All four pass full parity, repeat/input/canary checks and post-timing parity on this fixture.

This narrow synthetic input range is not captured model data or a universal exactness/quality guarantee. Faster FP16-output timing remains explanatory, not precision-preserving evidence. Independent actual reviews passed; V2 cleanup ended at **46 C**, API stopped. [Metrics and hashes](metrics.json) retain both attempts. The [earlier F16 experimental-option verdict](../2026-10-12-gfx906-c183-prompt-f16-abba/README.md) remains unchanged.
