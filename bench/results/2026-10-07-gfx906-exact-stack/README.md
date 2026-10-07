# Clean exact decode stack

Frozen baseline82f4473, source-only combination of:
- GPU Q2 mode16:3386781 (iq_kernels.cu).
- Selected-width CPU Q2 AVX2 spread:9fe5747 +86ebe00; CTest integration2d9788a.
- Graph-safe guarded gfx906 top-k:5d5e60a +0a64615; regression integration8dac611.

No SGEMM/FP16, MMVF tile, HC-up, paired-row CPU, scatter, KV DMA, or helper
experiment is imported. Existing deployment build/API patches must be applied
separately and recorded by hash; they are not research optimizations.

Runtime selection: STRATA_EXP_MODE=16, STRATA_Q2_AVX2_SPREAD=1,
STRATA_GFX906_TOPK_REG=2 plus the baseline's seven qualified settings
(mode16 replaces mode15). MTP16K and normal GPU HIGH are separately measured
machine-specific settings, not source patches.

Fresh clean-build and end-to-end qualification pending. Do not treat this source
snapshot as a promoted production binary.
