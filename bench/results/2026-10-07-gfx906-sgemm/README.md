# Selective gfx906 SGEMM investigation

Based on upstream PR1123, retaining its four original-author commits.
Two gfx906 16GiB cards, pinned ROCm7.14 image used by the Hybrid deployment.
Baseline:82f4473. Whole-model configuration unchanged so far.

## Micro screen, original upstream route

Each GPU, native/SGEMM/SGEMM/native, seven synthetic matrix shapes, true Gemm calls.
Per-shape times: median of five ten-call event-timed batches, after three warmups.
Widening costs included. Samples are independent processes; clocks not locked.

- BF16 HC down, T4096 N320 K10240:1.40x /1.38x speedup on GPU0/1
- BF16 HC up, T4096 N10240 K320:1.90x on both
- BF16 HC down atT256:1.40x /1.39x
- FP16 small expert-like matrices: up to1.94x slower with SGEMM
- FP16 dense T4096 N12288 K2560: about3-7% slower

Generic enable-everywhere SGEMM is therefore not selected.
The new opt-in STRATA_GFX906_HC_SGEMM=1 routes only those two BF16 HC shapes.
Native defaults unchanged; upstream's broad STRATA_RDNA2_SGEMM flag remains separate.

All eight original parity invocations and eight microbench invocations passed.
Original parity checks entire small/cross-slice shapes vs FP64 and output canaries.
Microbench checks64 output samples per shape vs FP64 plus all outputs finite.
Thresholds: relativeL2<1e-4, maxabsolute<5e-3 on uniform[-.25,.25] operands.
This is not a bitwise-equivalence claim or model quality qualification.
Exact widening preserves operands; SGEMM changes floating-point summation order.
Additional actual-HC shapes and a cross-slice padded-beta case are now added;
selected-route rebuild and full-model A/B still pending.

Full micro results:micro.json. Benchmark source:bench/gfx906_gemm_screen.cpp.
