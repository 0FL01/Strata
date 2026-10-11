# c183 PP value-load lookahead: slower component

**REJECT_PP_LOOKAHEAD_PERFORMANCE.** One value-only four-cell lookahead candidate preserves the FMA sequence, score and softmax. It was compared with the original c183 archive, query swizzle/reduce12 ON, on gfx906 owner0.

Full output and scratch byte parity passed in direct and captured execution for three finite synthetic cases: nq1/context4; masked nq33/context4096/cap2051; and nq32/context65536/cap2051/chunks33 (Q24/KV2/head dimension256). Canaries and input immutability passed.

The last shape used 16 warmups and eight alternating pairs (**four AB, four BA**), with 16 graph calls per sample:

- Baseline full-batch median: **0.754356 ms**
- Candidate median: **0.805721 ms**, or **6.809112% higher latency**
- All eight baseline-minus-candidate savings are negative; paired median **−0.051430 ms**, against the predeclared **+0.240 ms** conditional 3%-PP relevance bar

All pairs are retained. **Park this candidate:** no engine patch, model run, timing retry or variant sweep. Warm repeated selection/pools are not cold/interleaved model work; these results establish neither universal cache behavior nor model performance.

Independent actual-runtime audit: **116 checks PASS**. Cleanup passed, API stayed stopped, final maximum sampled temperature **46 C**.

[Aggregate metrics and provenance hashes](metrics.json). No production change or PR.
