# gfx906 Hybrid performance campaign

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
