# Rejected gfx906 cell-major attention probability layout

Hypothesis: prefill on gfx906 uses the FP32 chunk+merge decode-attention kernels in 32-query groups. Its value loop loads twelve head-major probabilities per cell. Reuse the dead aligned query shared array for cell-major probabilities, loading the same twelve floats as three float4 values. This isolates that storage change from the existing pre75 implementation; it does not import its score reductions or V prefetch. All score, exp, reduction, V-load, cell-order, FMA and merge operations remain unchanged.

The candidate is opt-in, gfx906 INT8 only, n_q > 8 and lane-cell off. Current production verify/MTP windows remain on the old specialization. Default dispatch is unchanged. No new persistent allocation or shared/global scratch capacity is required.

## Cheapest falsifier

The compiler reports identical resources for old/new INT8 kernels: 41 VGPRs, 42 SGPRs, four waves/SIMD, 15,872 bytes LDS, no spills or scratch. Extracted gfx906 ISA confirms vector shared-memory loads in the candidate. That is not a performance claim.

GPU0 ABBA, separate processes, 32 queries at context 65,536, selection cap 2051, actual model page size 4, 24 query heads, two KV heads, dimension 256. Each process uses three warmups and 20 event-timed full chunk+merge calls. Inputs are deterministic, pages shuffled, outputs sentinel-checked. All 786,432 output bytes match across arms, as do input hashes. Dispatch trace verifies the requested specialization actually ran.

| Arm | Median milliseconds |
|---|---:|
| A1 old | 1.191599 |
| B1 cell-major | 1.208079 |
| B2 cell-major | 1.209440 |
| A2 old | 1.191599 |

Mean candidate latency is 1.2087595 ms versus 1.191599 ms, equivalent to 1.42% lower component throughput. Both orderings agree. The change is rejected on speed, despite passing this fixture's full-output bitwise check. The planned 10% component-gain gate was not reached; no second-card expansion, large parity matrix or model benchmark followed. The candidate engine was never linked or deployed. RND kernel/CMake files were restored, and the existing live API was restored successfully.

This is a synthetic component result, not a universal parity or end-to-end speed claim. The full pre75 kernel and other layouts are not ruled out by this isolated test, but no cosmetic sweep is justified by it.

Parent candidate remains the separately qualified HC+MMQ build. Patch SHA256: 71b3a0e7a9ac843fe19d31bd04acd54252fa3e099a7d30900882afd85b912557. Probe SHA256: 6ee396eef779c288162f1dda1d9be3af17c8e2cf411f15d02db28e83bb1fac7e. Pinned llama.cpp: 3cf03257f219afbe7334045ff7c6a06ac68c627d.
