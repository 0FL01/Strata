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

## Model and follow-up screening

Selective-route checks passed on both GPUs, including actual HC shapes, padded output
with beta1, and a3300-row HC down product crossing the activation slice boundary.
Engine SHA256440fb79cf860bb43c96df3c3332754cf9c71c6bf4c3e55f096d10563ea63d769.

Cold-process ABBA,2048 outputs:4K baseline PP348.21/348.04, candidate317.69/353.66;
64K baseline597.71/599.23, candidate630.70/598.11. This is not a stable gain.
Each arm repeats the same output; A/B first differs at output16(4K) and234(64K).
TG comparisons therefore are not matched-output speedups.

Odd dimensions are not the explanation in isolated kernels:4095 HC down still gains
about1.38x and HC up1.88x;1535/3071 also improve. First-call wall costs are about
one second for both routes, while warm calls take milliseconds.

Four no-cache requests per process,4K/512 outputs, A-B-B-A:baseline warm PP356-359;
candidate often375-381, but one warm request falls to339.6. All requests explicitly
report zero reused tokens and4096 read tokens. Cold startup alone cannot explain
the remaining variability. Allocation fallback and phase costs are being instrumented;
they are hypotheses, not established causes. No production promotion.

See model-evidence.json for every measured phase and output hash.

## Scratch reuse experiment

Instrumented4K and64K runs used every selected SGEMM call, with zero allocation
fallbacks. The intermittent slowdown is not silent fallback to native GEMM.
The original route allocates13,107,200 weight bytes and134,184,960 activation bytes
per stage. This is about140.47MiB per GPU beyond the existing prompt workspace.

Reusing only the64MiB dequant scratch was tested first (BORROW=1). Its1024-row
down slices slowed HC down from about7.6 to11.0ms; not selected.
BORROW=2 instead uses the attention/MoE region while it is idle during HC.
It retains the original slice shapes and needs no extra matrix buffers.
The region is cleared from the handle before its next phase; its uses share the
compute stream. Peer/helper paths retain the original allocation route.
Input/weight/output overlap with a borrowed region refuses borrowing.

Native, owned-SGEMM and arena-SGEMM component checks passed on both GPUs.
Added alias refusal cases for each input/output and both possible scratch regions.
Arena microbenchmarks retain about7.58ms down and3.37ms up atT4095, with53/53
borrowed calls and zero owned matrix-buffer capacity in each standalone case.
These remain numerical-tolerance checks, not model quality equivalence.
Whole-model warm and64K comparisons of arena reuse are pending.
