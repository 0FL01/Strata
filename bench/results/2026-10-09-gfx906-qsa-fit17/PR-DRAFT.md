Implementation: [6868ebdfbd13daf3c5fcd6106c15feccc1419d22](https://github.com/0FL01/Strata/commit/6868ebdfbd13daf3c5fcd6106c15feccc1419d22).

Review the [incremental diff against ca353315](https://github.com/0FL01/Strata/compare/ca3533157d066a13b128f3daa61f56411dcf3155...6868ebdfbd13daf3c5fcd6106c15feccc1419d22). This is a stacked follow-up to [PR #1535](https://github.com/Niko1221/Strata/pull/1535); its dependency remains part of the upstream-main comparison until integrated. This file is the prepared PR description, not a newly created upstream PR.

Title: gfx906: right-size guarded QSA top-k to 17 keys near 64K

Depends on #1535 (currently unmerged); this branch starts at its ca353315 head. The incremental change can be reviewed against that branch. It does not depend on query-swizzle or reduce12.

## Summary

Add default-off STRATA_GFX906_TOPK_FIT17=1 to the guarded STRATA_GFX906_TOPK_REG=2 route. The exact existing selector uses 17 slots per thread when all current device rows fit 17,408 blocks; larger windows keep register66. The reference short-context guard and all existing fallbacks remain. No selection arithmetic or output ordering changes.

The scalar bound includes 69,631 cells; 69,632 needs another slot even with an empty tail. Device-side max across at most eight rows supports unsorted batches and graph growth/restores. Optional trace reports enabled topology only.

## Validation

Public selector TU/header build, directly linked without a private support archive: 46 correctness and 8 component ABBA processes passed on both gfx906 cards. Public default-off kernels match the public base; actual device instructions and resources match the separately qualified integration selector. Component latency decreased 25.73%/26.06%. The original 30% engineering screen remains negative.

Separate integration-binary model ABBA: +1.41% TG with suffix disabled and exact IDs/counters; +1.30% on the ordinary adaptive profile with exact IDs/topology, while second-pair draft/cache counters differed and are disclosed. These are not full-public-engine measurements or constant-workload attribution for the adaptive result.

Scalar scratch falls from 1,048 to 56 bytes/lane. The wide fallback still has 1,048 bytes scratch and +12/+1 SGPR/VGPR spills versus the original route, plus extra guard/launch work. CUDA/non-gfx906 runtime and broad model coverage are not claimed.

See [implementation report](https://github.com/0FL01/Strata/blob/6868ebdfbd13daf3c5fcd6106c15feccc1419d22/bench/results/2026-10-09-gfx906-fit17/README.md) for exact bounds, raw component medians, model scope, provenance and limitations.
