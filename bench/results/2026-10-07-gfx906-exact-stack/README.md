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

## Fresh build and component gates

Source b6731bf was archived and transferred byte-for-byte to a new directory.
The four pre-existing deployment build/API patches were applied separately.
No research object files were reused. Same pinned container/toolchain and
llama.cpp dependency as the measurement epoch.

Build succeeded; executable SHA:
ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14

Passed CPU spread/AVX2 CTests, grouped parity and guarded top-k on each GPU,
and72 real-weight mode15-versus16 cases (layers0/23/47, groups1/8/32,
token widths1/2/4/8, fusion enabled). The fused path does not write h scratch,
so that scratch is not counted as an independent SwiGLU oracle; active Q8,
gate/up and final expert output comparisons are meaningful.

Full-model comparison against the original production executable, actual200K,
and API qualification are pending. This is not a production promotion.
See components.json for source/deployment patch hashes and invocation receipts.
