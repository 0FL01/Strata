# gfx906 c183 HC injection N4: finite-corpus parity, V1/V2 speed results

**V2 passes the finite parity corpus and is faster in all 32 component timing pairs.** Reference medians are **3.990–4.000 ms**; candidate medians **0.959–0.965 ms**, a **4.14–4.17× reference/candidate median-time ratio**. This measures the complete two-kernel candidate path, not model or whole-prompt speed.

Both versions pass **214 cases / 3,505,748 finite FP32 elements**: 192 actual-weight cases across **T4096/4095, N4, K10,240**, four tiny-coefficient one-hots and 18 finite adversaries. Two direct BF16 controls, four pre-timing cases and four post-timing full-buffer checks also pass.

**V1 remains a speed rejection:** all 32 event and wall pairs are slower, with candidate/reference median-time ratios **2.589–2.644×**. Its correctness result is retained separately.

Unlike the [failed scaled-FP16 route](../2026-10-12-gfx906-c183-hc-inject-exact/README.md), these candidates retain BF16 operands. The ISA-derived design preserves cyclic **GSU3** K splits, ordered lane-local FMAs and FP32 post-reduction order/modes. V2 changes input loading to cooperative **K16 staging**, using **4,352 bytes LDS and two unconditional CTA barriers**, without arithmetic reassociation.

Timing uses **16 warmups per arm and eight alternating AB/BA pairs per case**. [Metrics](metrics.json) define ratios explicitly and retain event/wall summaries. Independent actual audits passed; both runs cleaned up at **47 C**, API stopped. This finite component corpus does not establish universal/NaN equivalence, general quality or end-to-end gain. No integration or promotion is implied; weights and output arrays remain private.
