# c183 draft-head exposure: park below 1%

One synthetic exposure screen on draft-owner GPU1 reused the original c183 kernels/core with a new host-only probe. The fixed hot row contains 106,299 FP32 logits; each stage used 128 captured serial primitives/pairs, 16 warmups and nine event batches. All six semantic fixtures passed.

- Greedy median: **35.141 us**
- Probability median: **35.229 us**
- Greedy + probability pair: **70.156 us median / 70.525 us maximum**

Using the conservative, source-derived **1,134-call scenario bound** (not a measured count), the maximum pair timing projects to **79.975 ms**, or **0.420242% linear wall share** against the historical normal c183 **19,030.8 ms** model reference. This is below the frozen **1%** prioritization filter: **DEPRIORITIZE_BELOW_ONE_PERCENT**. Park head sampling; no optimization or model screen follows from this exposure.

This conditional hot-buffer projection is not a rigorous model critical-path ceiling or a measured speedup. Real logit distributions, interleaved MTP layers and critical-path effects differ; host dispatch is not credited.

Independent actual-runtime audit: **121 checks PASS**, including all 27 event batches, exact live/atomic/terminal bindings and cleanup. API stayed stopped; final maximum sampled temperature was **47 C**. No production change or promotion.

[Aggregate metrics and source/audit SHA-256 hashes](metrics.json). Raw payloads and private runtime identifiers are not published.
