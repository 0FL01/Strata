# Opt-in gfx906 Q5 head R2

Base: `413dbf648b0b59014c3d3a648ab068f5fbc9e444` ([PR #3094](https://github.com/Niko1221/Strata/pull/3094)). This is a checkpoint of local R&D, not a claim that the new change alone exceeds 3%.

## Scope

Only two source files change. The new dispatch is disabled by default. Set `STRATA_GFX906_Q5_HEAD_R2=1` to select two rows per wave for Q5_K head shapes 2560 x 248320 and 2560 x 106299, with columns 1, 2 or 4, on actual gfx906 wave64 devices. All other shapes, columns and targets retain their existing paths. `STRATA_MMVQ_WAVE=0` still disables this path. Wider prototype dispatch regressed at columns 3 and 5, so those are excluded. Per-row arithmetic/reduction order is unchanged.

## 64K model results

Eight cold-process runs in ABBA + BAAB order, 65536 input / 1024 output, greedy, all output IDs exactly equal:

| Profile | PP t/s | TG t/s |
|---|---:|---:|
| Frozen control | 653.32473 | 61.63579 |
| Q5 R2 + fast norm + auxiliary CPU setting | 657.00448 | 62.62231 |
| Relative change | +0.5632% | +1.6006% |

Throughput is total tokens / total measured time. All four TG pairs improved; three of four PP pairs improved. One reverse-order PP pair regressed. PP variability remains unresolved; these numbers do not establish universal no-regression performance.

Separate controlled comparisons (do not add percentages):

| Change | PP | TG |
|---|---:|---:|
| Q5 R2 alone | -0.5703% | +1.0309% |
| Existing fast norm alone | -0.7421% | +0.9401% |
| Q5 + fast norm | -1.0700% | +1.7204% |
| Existing auxiliary CPU setting alone | +0.6095% | -0.6696% |

This combination is an opt-in preset for the tested server, not a universal gfx906 default. No auxiliary-affinity or norm kernel code changes are included.

## Component validation

Run the existing benchmark target, once per card:

```sh
b6_mmvq_bench 100 0 1 --q5-head-r2
b6_mmvq_bench 100 1 1 --q5-head-r2
```

Both cards passed: 256 case/width comparisons in total, bitwise equality and finite outputs. Coverage includes shared Q8 input bytes, R1/R2 comparison, R1 single-column reference, odd tails, columns 1-8 and unchanged fallback paths. Synthetic T4 component latency: main head about 2.84 -> 2.36 ms; MTP head about 1.25 -> 0.996 ms. These are component improvements, not model speedups. R2 resource inspection found no spills. Existing staged fast-norm parity/selftest passed on both cards, including graph replay.

## Preset and reproduction limits

Process environment:

```sh
export STRATA_GFX906_Q5_HEAD_R2=1
export STRATA_GR_NORM_FAST=1
```

Native generator protocol request:

```text
GEN 1024 temperature=0 top_p=1 top_k=1 seed=12345 aux_cpus=1 <comma-separated prompt token IDs>
```

Preserve identical model, inputs, all other flags and cache sizes across control/candidate. Compare complete output token IDs, not text snippets. Per-run results and output hashes are included; prompt contents are not published.

The existing `aux_cpus=1` feature is Linux/topology-specific. This server uses host CPU0, workers CPU1-15 and helpers CPU16 (CPU0's SMT sibling). Eligible driver threads can also move. Request-level changes can persist until another request changes them; restoration/new-thread behavior is a limitation. This is not qualified for concurrent serving or other CPU topologies.

Test server: two Radeon Pro VII 16GiB, gfx906; Xeon E5-2698B v3, 16 cores/32 threads; ROCm7.14, Clang23. Q2_0 experts with Q8_0 PLE; int8 KV; resident context32768, max context262144; expert slots9399+8619=18018; pipeline2, split27/21, prefill4096, spec6, MTP max4, suffix off. Detailed fixed knobs are in manifest.json.

## Provenance

Frozen baseline binary SHA256:
`cc78113d53e5eb89146c1c45fccacef47cd89cba3fa39f7f4b59927c7a384b58`

Candidate binary SHA256:
`23ffbb6d7fdedc87637c382499f79b7dec7e55f3f05f00241b41196935a482de`

Candidate archive SHA256:
`9caf367f890e0bb821fb6658e672714d5da328c73603517d8f2adc05e983025b`

Frozen baseline archive SHA256:
`05e4c669013c348f1577c8996a219d7600c5cacf6e367f97dd075b5ab521446a`

Archives, exact binary/configuration and full raw evidence are retained on the test host. Candidate archive depends on the frozen baseline archive for unchanged sources/dependencies. Local source audit found only the two expected source changes; normalized build recipes/configuration matched. Historical object identity is not established.

This published branch is based on PR3094 and keeps its HIP build prerequisites in a separate evidence patch. It has not been independently rebuilt/tested as a public checkout. Model results come from the local validated baseline plus this exact two-file patch. No CUDA/other-GPU runtime, sampling, concurrent-serving or full262144-context qualification is claimed. The previous baseline remains preserved.

## 200K qualification

One preliminary cold-process A/B pair, 200000 input / 256 output: PP 609.51415 -> 617.76863 t/s (+1.3543%); TG 53.82222 -> 54.94388 t/s (+2.0840%). All 256 output IDs matched both the current frozen control and the historical0705 golden. RESUME/REUSED were zero and all200000 input tokens were processed. This is not a repeated throughput claim.

Inherited HIP build prerequisites: [compatibility patch](../2026-10-18-gfx906-exact-pipeline-j48/compatibility-prerequisites.patch).
