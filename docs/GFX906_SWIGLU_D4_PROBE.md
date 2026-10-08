# gfx906 SwiGLU D4 component results

8 October 2026

**Decision: retain the validated component port and defer model integration.** Fusing MMQ SwiGLU with D4 activation quantization produced byte-identical output on both tested gfx906 GPUs and approximately **1.9× component speedup** at 32,768 expert-token rows. The corrected call-count model predicts only **0.2–0.4% overall prompt-processing benefit** for the evaluated long-prompt workload. That overall effect is an estimate; no model callsite was added and no end-to-end speedup was measured for this port.

## Scope and correctness

The component replaces `mmq::swiglu` followed by `mmq::quantize`. Its input is FP32 gate/up data with 1,280 columns, producing 640 activation values per row, quantized into the D4 layout with columns padded to 1,024. The actual model down type, Q2_0/type 42, uses D4 in the pinned llama.cpp revision.

Both GPUs passed:

- **Strict gate:** 54 executed cases, including 18 mandatory type-42 cases; zero differing bytes and unchanged guards.
- **Benchmark gate:** 64 executed cases, including 28 type-42 cases and 10 timing cases. Every timing case passed byte checks before and after timing.
- Coverage: Q2_0, IQ4_NL and Q8_0; split and interleaved gate/up; rows 1, 37 and 4,113; random, zero and outlier inputs. Checks cover all output bytes, padded blocks, the reserved tail and prefix/suffix guards. Missing devices or ineligible required types fail rather than silently skip.

The opt-in gate retains both supported-type and D4-layout eligibility. The gate-off check also passed. No combine/hyper-connection fusion, MMQ tiling changes or model callsites are included.

## Measured component timings

Two separately selected gfx906 wave64 GPUs were tested. The runtime reports `AMD Radeon Pro VII`. Times below are median microseconds per invocation; speedup is the median of paired baseline/fused ratios. Measurements use seven alternating-order pairs of 40 repetitions after warmup, with stream events. These are direct component launches, not model-level or graph-replay measurements.

| GPU | Expert-token rows | Gate/up layout | Baseline µs | Fused µs | Paired speedup |
|---|---:|---|---:|---:|---:|
| 0 | 37 | Split | 7.372 | 3.512 | 2.100× |
| 1 | 37 | Split | 7.348 | 3.504 | 2.097× |
| 0 | 4,113 | Interleaved | 95.800 | 52.540 | 1.826× |
| 1 | 4,113 | Interleaved | 95.444 | 52.324 | 1.821× |
| 0 | 32,768 | Split | 705.248 | 376.368 | 1.874× |
| 1 | 32,768 | Split | 701.636 | 374.372 | 1.874× |
| 0 | 32,768 | Interleaved | 708.256 | 375.020 | 1.889× |
| 1 | 32,768 | Interleaved | 705.049 | 372.880 | 1.891× |

Additional timing shapes were 1 and 256 rows. The largest case used approximately 312 MiB of explicit device buffers and 160 MiB of peak host buffers.

## Corrected model impact estimate

The frozen source defines **K=10**, not 8 (`src/prefill/prefill.cpp:93`), and rejects a different routing K at initialization (819–820). A full 4,096-token layer therefore processes **40,960 expert-token rows**. Grouping partitions those rows exactly once (2620–2656); it does not duplicate them.

Calls occur once per group of up to 16 routed experts (733, 3029–3047). If all 512 experts are routed, there are **32 calls per layer**, averaging **1,280 rows per call**. MMQ's `max_rows` and tile padding do not inflate this component's row count. Quantization pads columns only.

A launch-plus-row timing model, checked against both the small and large component measurements, estimates roughly **0.51–0.52 ms saved per layer**. For 16 chunks, a 27-layer primary stage and 21-layer secondary stage:

- Primary-stage work plus the final secondary drain: approximately **0.23 seconds**, or **0.22%** of a roughly 105-second prefill.
- Summing all stage work without overlap: approximately **0.40 seconds**, or **0.38%**.

The source overlaps different chunks across stages (3248–3257), so the serialized figure is deliberately conservative. These estimates assume eligible MMQ layers, 32 groups and approximately affine component costs. They are not hard elapsed-time bounds; routing imbalance and host submission behavior can affect the result. Even modeled elimination of the entire baseline component accounts for only about 0.5% of pipelined prefill time, or 0.8% when summing all work without overlap.

The evidence supports preserving this exact gfx906 port while prioritizing larger bottlenecks. A future integration would still need model-level correctness and performance validation.

## Provenance

- Donor: PR #1525's [Niko1221/Strata commit](https://github.com/Niko1221/Strata/commit/f048d15594c62335b9fa7c350ecf4d07b749d30d), `f048d15594c62335b9fa7c350ecf4d07b749d30d`. Only the MMQ SwiGLU/D4 kernel, API and adapted component test were extracted. The kernel and launcher match the donor exactly.
- Base: `f152172332693c933b8a3104ce193d8a4315c2b4`.
- Tested component commit: `895801834ad8ba0acf7bb432565dd18372de00a6`.
- Pinned llama.cpp: `3cf03257f219afbe7334045ff7c6a06ac68c627d`; [type-42 definition](https://github.com/ggml-org/llama.cpp/blob/3cf03257f219afbe7334045ff7c6a06ac68c627d/ggml/include/ggml.h#L432) and [D4 mapping](https://github.com/ggml-org/llama.cpp/blob/3cf03257f219afbe7334045ff7c6a06ac68c627d/ggml/src/ggml-cuda/mmq.cuh#L60-L64).
- Target: `gfx906_swiglu_quant_probe`; build and all recorded runs exited successfully.
- Tested binary SHA-256: `da106391e14aec9d524d12eced3446a006b8838edd80e14bace52259a43637d1`.

## Component reproduction

Build the `gfx906_swiglu_quant_probe` target in the pinned gfx906 environment described above. Run with `STRATA_GFX906_MMQ_SWIGLU_QUANT=1`, first without `--bench` on each GPU, then with `--bench` only after both strict gates pass. The gate-off test is `gfx906_swiglu_quant_probe --gate-off` with the variable unset. Preserve complete output and the exact executed-case counts. This branch contains no model callsite; setting the variable does not accelerate the model by itself.
