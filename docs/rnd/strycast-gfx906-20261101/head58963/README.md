# Narrow 58963-token Q5_K head qualification

This is a fixture-specific gfx906 R&D harness, not a general model benchmark.
It links the same production strata_kernels and strata_core archives as the
candidate engine. It does not copy device kernels. The public source deliberately
excludes private fixture paths/stat pins, weights, logits and container commands.

1. Run verify-fixtures.py --gguf MODEL --vocab MAP --output-dir PRIVATE --seal.
   The bounded GGUF parser verifies the exact output tensor and canonical map.
   Re-run without --seal before and after GPU tests. Do not reuse stale pins.
2. Compile the C++ file with the candidate's mmvq_multi_parity compiler flags,
   generated fixture-pins.hpp include directory, and same link libraries plus
   -ldl. Preserve the ELF symbol table; the harness checks actual captured
   kernel identities, not merely selector intent.
3. Use the frozen effective engine environment, explicitly setting
   STRATA_GFX906_Q5_HEAD_R2=1, STRATA_MMVQ_WAVE=1,
   STRATA_MTP58963_BASE_R2=0 or 1. The latter chooses contiguous R1 or R2
   against indexed R2. Existing full-head dispatch is unchanged.
   Run --device 0 --iters 200 --reverse 0 --gguf MODEL --vocab MAP --dump FILE,
   then device1/reverse1, for both baseline values. Buffers require ~550MiB.
4. Require successful exit and identical full framed dump SHA-256 across all
   four runs. Every run checks 58963 logits, output guards, immutable full/gathered
   weights/map/Q8 inputs, three finite input patterns, direct and graph replay,
   post-timing outputs, 14 host-rejected invalid calls and actual kernel grids.

GPU graph timings are the cleaner component metric. Direct event timing also
includes per-launch selector mutation/host enqueue effects. Neither establishes
end-to-end performance or full inference/cache correctness. This harness does
not test real hidden-state distributions, owner destruction, cancellation or
undo/rebranch; those remain engine-level gates. No NaN inputs are admitted.

Observed fixture: full Q5_K head SHA256
93f1c7cb7a7cf8134ce9f8cf80c5416df968f7f1ddcc16f2159a9521080826a5;
canonical map SHA256
25d7fd1670a2e0ec885868d1718d410a3baab03bceeacf0a156cf93ffe4e1ef4.
No model payload is distributed.
