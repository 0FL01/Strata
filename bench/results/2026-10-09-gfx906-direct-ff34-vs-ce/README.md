# Direct combined comparison and public reduce12 component evidence

## Direct combined model comparison

Fresh-process A1/B1/B2/A2, 65,536 prompt tokens and 1,024 generated tokens per arm. PP is the native prompt count divided by prompt time; TG is actual outputs divided by native decode time. Means are arithmetic means of arm rates. Loading and request wall times are separate.

| Native tokens/s | Optimized stable A | Whole combined candidate B | Direct gain |
|---|---:|---:|---:|
| PP | 598.287886486 | 646.760686255 | +8.101919% |
| TG | 50.531488516 | 53.083264106 | +5.049872% |

Both pairs are positive: PP +8.152706%/+8.051164%, TG +5.139453%/+4.960404%. All four complete 1,024-token ID arrays match exactly, as do accepted/offered/cache-hit/lookup/prompt-read/reuse counters. The [numeric receipt](numeric-results.json) preserves the complete arrays and raw durations/rates, without private infrastructure paths, filesystem provenance, configuration hashes or service-operation details.

This is the whole combined candidate against an already optimized baseline. It is not a stock-upstream comparison and these gains cannot be attributed to the reduce12 PR alone. The separate frozen-stack isolated reduce12 ABBA measured +3.440197% PP/+1.581280% TG. One ABBA is not a confidence interval or broad workload qualification; exact IDs apply to this fixture.

Thermal summaries retain 27/28/27/27 samples by arm and largest observed sample gaps of 9.998/6.628/9.448/9.186 seconds. Overall observed maxima are 60/80/63 °C for the three sensors. These are discrete observations. Raw critical-temperature limits were not retained, so a critical-minus-10 °C margin cannot be independently recomputed.

## Separate public-source component check

[Public numeric/ISA receipt](../2026-10-09-gfx906-qsa-reduce12/public-component-numeric.json) and [PR description](../2026-10-09-gfx906-qsa-reduce12/PR-DRAFT.md).

Exact public QSA translation unit plus unchanged published probe, linked with the old QSA object removed from a frozen support archive. This is an isolated component build, not a full public-tree build. Source [commit 08a844d3](https://github.com/0FL01/Strata/commit/08a844d3f31199798b7ea78dc5c8512fd9c17e79) is a one-file +74/−3 follow-on to #1661.

At nq=32/context=65536, 50 timed repetitions per process, A1/B1/B2/A2:

- GPU 0: 1.0384395 → 0.7608800 ms, latency −26.728519%
- GPU 1: 1.0323620 → 0.7586825 ms, latency −26.510032%

All full outputs match between arms and GPUs, including nq=1/context=4 and masked-page nq=33/context=4096 cases. The receipt retains all full-output hashes; output byte files themselves are not embedded. Separate trace smoke confirms selection. Actual compiled full-kernel shuffles 70→26, score shuffles/adds 60→16, dot FMACs 84→84; VGPR42→48, SGPR42→43, occupancy4 waves/SIMD, LDS15872 bytes, zero scratch/spills. These are component latency reductions, not model-throughput gains.

## Offline numeric validation

From this archive checkout root:

```sh
python3 bench/check_gfx906_public_numeric.py bench/results/2026-10-09-gfx906-direct-ff34-vs-ce/numeric-results.json bench/results/2026-10-09-gfx906-qsa-reduce12/public-component-numeric.json --selftest
```

This derivative's validator checks arithmetic, full model ID/counter parity, component output-hash equality, selection/exit status and recorded ISA resources. Its 12 intentional corruptions are rejected. It does not validate omitted manifests, private configuration restoration, underlying output bytes, or a full public-tree build, and cannot authenticate measurements without trusted original evidence. No new hardware runs are performed by this validator.
