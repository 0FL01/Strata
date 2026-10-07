# gfx906 Hybrid performance campaign

## Final selected settings

The final 16-process comparison uses the original `cc7eeb6` engine in both
arms (SHA256 `3fdb12152c5e148c7af241cc4cde0e4f71494f657bba48f6ca9bb363b90757f6`).
Only the seven environment values in `candidate.env` change. No weight/KV
quantization, model, context, sampling or placement policy is changed between
arms. The candidate combines mode15 Q2_0 down unpacking, multi-row BF16 GEMV,
SwiGLU/Q8 fusion and the exact-consumed-output GDN prefill path.

ABBA, two fresh processes per arm for each workload, 2048 output tokens each:

| Workload | PP before | PP after | PP change | TG before | TG after | TG change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Code 4K, controlled | 338.87 | 348.46 | +2.83% | 49.957 | 52.416 | +4.92% |
| Code 64K, controlled | 582.34 | 596.67 | +2.46% | 47.852 | 49.167 | +2.75% |
| Russian 64K, controlled | 581.44 | 598.27 | +2.89% | 45.793 | 48.019 | +4.86% |
| Code 64K, adaptive/sampled | 580.76 | 595.64 | +2.56% | 44.462 | 47.315 | +6.42% |

Controlled means fixed expert placement and greedy sampling. All 2048 IDs
match across all four runs in each controlled workload. Every candidate run
beats both baseline runs in PP and TG at its workload. The code-64K candidate
TG range is 48.463–49.891: retain that variation rather than extrapolate a
precise universal percentage.

The last workload uses normal adaptation and production sampling 1/.95/20,
seed12345. Its outputs differ, including the two baseline repeats, so +6.42%
is observational throughput and not equal-work completion or a quality score.
No Russian draft-vocabulary changes were used. `final-comparison.json` and
`final-results.json` retain every phase duration, rate, counter and output hash.

This does not establish arbitrary-prompt quality equivalence or performance
on other machines. Capacity and live API verification are recorded separately.

Baseline: `cc7eeb6`, the opt-in Q2_0 gate/up and down patch on upstream
`82f46a8`. Two MI50-class gfx906 16 GiB cards, Xeon E5-2698B v3,
128 GB RAM, HIP 7.14.60850. Model: shefowl Flash-Next Hybrid
IQ3_XXS/Q2_0, revision `55568c1b41d2e381a59a281447fb10935c3c6d0a`.

These measurements were obtained with AI-assisted engineering on the actual
two-card machine. Hypotheses below are not upstream or universal speed claims.

## SwiGLU and Q8_1 fusion

Only `STRATA_HIP_SWIGLU_FUSED` changes between the two arms. Both use expert
mode 13, split 27/21, INT8 KV with 32,768 resident tokens, 204,800 context
capacity, prefill chunk 4096, MTP cap 4 and suffix lookup 3. Native text serving,
vision disabled, fixed expert placement (`--adapt-every 0`), greedy sampling,
seed 12345, fresh process per run, prompt reuse disabled. The configured window
is capacity, not a full-window qualification. Clocks are not locked; page cache
is uncontrolled. No competing inference workload.

Three runs per arm per prompt size, ordered A-B-B-A-A-B; 2048 generated tokens
in each run. Rates below are total tokens divided by total native phase time.
Startup is excluded. Every output token ID matches across all six runs at each
prompt size. Expert placement and accepted/offered draft counters agree.

| Prompt | TG baseline | TG fused | Change | PP baseline | PP fused |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 49.830 | 50.121 | +0.584% | 338.591 | 338.391 |
| 65536 | 47.882 | 48.009 | +0.265% | 581.052 | 582.790 |

Per-arm TG ranges overlap. This is a small observed positive delta, not a
demonstrated stable speedup. Fusion affects decode kernels, so the PP difference
is not attributed to it. Machine-readable rates and individual TG values are
in `fusion.json`. The tested engine SHA256 is
`3fdb12152c5e148c7af241cc4cde0e4f71494f657bba48f6ca9bb363b90757f6`.

### Correctness before performance

The grouped parity test additionally compares the active Q8_1 bytes. It does
not compare the fused path's unwritten floating-point `h` scratch or inactive
Q8 rows. Added the actual Q2_0/Q2_0 H=2560, FF=640 shape; the graph microbenchmark
uses that shape too. All format combinations, empty calls, nonzero entry
offsets, scattered output rows and stale scratch passed on both GPUs with
expert modes 13 and 15 and fusion enabled: four complete test invocations,
zero failures. Synthetic checks do not establish model quality independently.

## Next hypotheses

- Independent shared-expert streams and MTP branch streams: gfx906 uses a
  separate backend macro from the normal HIP build. PR #1240's normal-HIP
  unused-stream guard does not directly change this configuration.
- Existing two-window pipeline: account for reduced expert-cache capacity
  before interpreting token differences.
- Upstream #1120: overlapped stage hand-off; test timeout recovery as well as
  throughput before adopting.
- Upstream #1181: output-equivalent linear GPU-plan construction; an engine
  improvement on this host still needs measurement.
- Upstream #1101: sleeping prefill stagers; relevance depends on which expert
  source path is actually used.

No new runtime default is changed by this checkpoint.

## Independent stream screening

Same baseline engine and fixed-placement controls as above, 65536 prompt and
2048 output tokens. A-B-C-D-D-C-B-A, two fresh processes per arm. Fusion remains
off. All output IDs match across all eight runs.

| Arm | Shared-expert stream | MTP shared branch | TG | PP |
| --- | ---: | ---: | ---: | ---: |
| A, current | 1 | 1 | 47.916 | 583.321 |
| B | 0 | 1 | 47.067 | 581.390 |
| C | 1 | 0 | 47.956 | 582.565 |
| D | 0 | 0 | 46.908 | 583.615 |

Disabling the main shared-expert stream loses about 1.77%; disabling both loses
about 2.10%. Disabling only the MTP branch is indistinguishable at this sample
size (+0.08%). The normal-HIP defaults do not improve this gfx906 backend.
Keep the existing stream settings. See `streams.json` for per-run values.
Some offered draft/look-up counts differ slightly despite identical output
IDs; this is not a per-kernel timing attribution.

## Two-window pipeline: do not promote

Initial ABBA screening (two processes per arm, 2048 output tokens) gave
50.102 -> 61.341 TG at 4K (+22.43%), but 47.796 -> 45.583 at 64K (-4.63%).
The extra pipeline allocations lower resident experts from 19078 to 18734,
so those output differences cannot on their own identify a pipeline defect.

Two stronger controls were run:

1. Equal cache counts: primary 9679, total 18734 in both arms, fixed placement,
   `STRATA_IQ_MT_MIN=1`. The serial arm uses later-stage reserve 761 MiB;
   pipeline uses 600 MiB. A first setup attempt at 760 MiB had one extra slot
   and was rejected before generating tokens. ABBA at 4K and 64K completed.
2. Identical pipeline allocations in both arms: `--pipeline-windows 2` with
   the documented debug request switch choosing `pw=0` or `pw=2`; primary
   cache 9679, later reserve 600, same CPU control. ABBA at 4K completed.

In both stronger controls, the pipelined output first differs at output index
93 on the 4K fixture. In the equal-cache 64K control it differs at index 13.
Serial repeats match each other. Equal counts do not alone prove byte-identical
residency maps; the identical-allocation control also removes that allocation
confound, but no root cause or quality loss is claimed from token divergence.
The advertised bitwise-equivalence expectation has not been reproduced for
this backend/model. Combined with the 64K regression, this blocks promotion.

`pipeline.json` retains each measured rate, cache counts, output-ID hashes and
first differing position. These are screening measurements, not a successful
quality qualification or a matched-token speed claim. The production pipeline
setting remains off.

## Upstream PR #1120: overlapped stage hand-off

Cherry-picked the four upstream commits through `202d4cc`, retaining original
authorship. Flag off/on ABBA, 2048 outputs at each prompt length, mode13,
fixed placement and greedy controls. Both arms use the same candidate binary.
All output IDs match within each prompt group.

| Prompt | Off TG | On TG | Change |
| --- | ---: | ---: | ---: |
| 4096 | 49.719 | 50.362 | +1.292% |
| 65536 | 47.838 | 48.026 | +0.392% |

Two runs per arm: the 64K effect is near the observed noise. PP is not improved.
See `overlap.json` for individual rates and exact binary hash. A dropped fifth
hand-off with `STRATA_SPLIT_WAIT_MS=2000` returned the expected native error
after 13 valid output tokens; the driver stopped that test and restored the
healthy authenticated image-capable service. This is a successful fault check,
not successful completion of the deliberately failed generation.

## Upstream PR #1181: linear expert planner

Cherry-picked `42d72ac`, retaining original authorship. The 4020-case planner
differential test passes on the host. Candidate binary versus the saved
pre-planner binary, #1120 overlap disabled in both, mode13, ABBA and 2048
outputs. All output IDs match at each prompt length.

| Prompt | Old planner TG | New planner TG | Change |
| --- | ---: | ---: | ---: |
| 4096 | 49.665 | 50.065 | +0.805% |
| 65536 | 47.883 | 47.725 | -0.329% |

This does not demonstrate a stable end-to-end gain on the target 64K workload.
No 64K acceleration is claimed. `planner.json` contains individual values and
the candidate hash. Source experiments are retained in the separate
`perf/gfx906-campaign` branch. This qualified-settings branch excludes both
PR #1120 and PR #1181 runtime changes.

## Multi-row BF16 GEMV: positive result

An isolated screening pass on the original baseline engine tested LFUSE,
GDN_SPLIT, PLE_BATCH, MMVF_ROWS and ATTN_LANECELL, each at 4K/1024 outputs,
between two baseline runs. All token IDs matched. This exploratory pass
(`exact-knobs.json`) selected MMVF_ROWS for replicated validation; it is not
evidence of a reliable gain for the other flags.

`STRATA_MMVF_ROWS=1` reuses the activation reads across four output rows per
block. The arithmetic order per output remains the single-row order.
Replicated isolated ABBA, 2048 outputs, same baseline engine and mode13:

| Prompt | Baseline TG | Rows TG | Change | Baseline PP | Rows PP |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 49.981 | 52.017 | +4.073% | 337.556 | 335.187 |
| 65536 | 47.816 | 49.313 | +3.130% | 583.110 | 583.045 |

Every candidate run beats both reference runs at its prompt length. All 2048
output token IDs match in all four runs for each length. The 4K PP variation
is retained rather than attributed to a decode-only switch. No PP improvement
is claimed. `mmvf-rows.json` contains the individual rates.

New `mmvf_rows_parity` tests the multi-row output against separate single-row
calls, including graph capture, row tails, output/activation strides, 1–8
tokens, nine shapes and three finite magnitude ranges. It also tests the
optional auxiliary-row entry point. Each GPU passes 432 cases comparing
1,660,200 output values including untouched padding, zero bit mismatches.
Run with `STRATA_MMVF_ROWS=1`. This validation does not by itself establish
all possible model workloads or full-window quality.

## Combined decode settings

At 64K/2048 outputs, mirrored A-B-C-D-D-C-B-A:

- A, rows only: 49.520 TG
- B, rows plus lane-cell attention: 49.526 TG
- C, rows plus expert mode15 and SwiGLU/Q8 fusion: 50.322 TG
- D, C plus lane-cell attention: 50.471 TG

All output IDs match. Two runs per arm, fixed placement and greedy. Attention
does not show a convincing independent benefit, so it is excluded. The final
candidate uses C. See `rows-combine.json`.

## Prefill GDN screening

The existing HIP recurrence test was made buildable under the separate gfx906
backend. On each GPU, all eight lengths (1,7,8,9,17,100,2048,2051), four candidate
variants versus the old path, passed: consumed FP16 output and final recurrence
state are bit-identical. The discarded FP32 output differs for the new norm
variants; it is deliberately not counted as an output contract.

An exploratory 64K/512-output screen on the unchanged baseline engine:

- Baseline PP: 580.56 and 583.05 tok/s
- GDN_HEAD=1: 591.27
- GDN_HEAD=1, GDN_PP=2: 596.74
- Above plus GDN_CONVL2=1 and GDN_NOY=1: 598.19

All 512 generated IDs match the baseline. This screen selects the last setting
for the final replicated comparison; the single-run prefill gain is not yet
a final qualification. See `prefill-gdn.json`.
