# gfx906 integrated R&D baseline

This main-branch integration collects the already reviewed, user-selected **f13a + KV prefetch + checkpoint-pool OFF** combination. It does not enable a new global preset, modify an installed configuration, deploy a service, or include the later adaptive HC retry experiment.

The parent is the published Q5-head-R2 branch including the reverse-proxy documentation fix. The old main (October 6) is an ancestor of that already-tested base: advancing main also brings 1,287 existing public commits and 2,836 changed paths from that ancestry, including API fixes. This is not a new update to the latest upstream head. The additional 19 implementation paths over that base match the tested f13a source exactly. Historical source/build validation is not a claim that a fresh build of this Git integration was run: this integration was Git-only.

## Included work

- Existing gfx906 prerequisites: exact HC F16/N4 prefill, QSA query-swizzle/reduce12, bounded FIT17, CPU Q2 spreading, J48 prefill, and Q5 head R2.
- Q8 output R2, exact router T1/T2 paths, Q2 GU chunk2, QSA rows and FIT17 tail/wide-scan selection.
- Omission of unused PCIe staging and stage-local verifier histories.
- Indexed MTP shortlist-head borrowing of the immutable original matrix while the main head retains ownership.
- Fixed-membership split26 mapping, explicit holes, logical holdouts and checked loan/refill handling.
- Payload-only checkpoint ownership transfer with exception-safe rollback.
- Existing KV-prefetch implementation selected by configuration, not a new kernel in this change.

These are the measured combination, not a sum of independent gains. Memory-saving changes also have individual latency tradeoffs. Existing unsupported paths retain their original fallback or fail-closed admission.

## Enablement and scope

The new experimental paths remain opt-in. Do not infer that merging this source activates them in an existing installation. Use the documented HIP build prerequisites in [EXPERIMENTAL_GFX906_PREFILL.md](EXPERIMENTAL_GFX906_PREFILL.md) and the existing gfx906 measured presets; validate the resulting build separately.

The selected experiment used two gfx906 GPUs, a fixed model/profile, native Q2_0 experts, `--prefill 4096`, `--spec 6`, `--mtp-max-t 2`, `--pipeline-windows 2`, `--no-coupled-draft`, `--kv int8`, `--kv-resident 32768`, and `--max-context 262144`. This is not qualification of arbitrary models, GPUs, batching or memory sizes.

Explicit performance selectors used in the combination:

```text
STRATA_GFX906_ATTN_QUERY_SWIZZLE=1
STRATA_GFX906_ATTN_REDUCE12=1
STRATA_GFX906_TOPK_FIT17=1
STRATA_GFX906_TOPK_REG=2
STRATA_GFX906_PREFILL_J48=1
STRATA_GR_NORM_FAST=1
STRATA_GFX906_Q5_HEAD_R2=1
STRATA_GFX906_Q8_OUT_R2=1
STRATA_GFX906_ROUTER_T1_ROWS=1
STRATA_GFX906_ROUTER_T2_EXACT=1
STRATA_GFX906_Q2_GU_CHUNK2=1
STRATA_QSA_ROWS=1
STRATA_GFX906_TOPK_FIT17_TAIL=1
STRATA_GFX906_TOPK_WIDE_SCAN=1
STRATA_HC_BF16_N4=1
STRATA_HC_F16_EXACT=1
STRATA_HC_F16_REGION_REUSE=1
STRATA_Q2_AVX2_SPREAD=1
STRATA_KV_PREFETCH=1
```

These selectors alone are not a complete portable launch configuration. The checked split26 experiment additionally required `STRATA_EXP_MODE=16`, `STRATA_MMVQ_WAVE=1`, `STRATA_NO_PCIE_GROUP=1`, `--pcie-frac 0`, `STRATA_MTP_HEAD_BORROW=1`, `STRATA_VERIFY_NO_PCIE_STAGING=1`, `STRATA_VERIFY_STAGE_HISTORY=1`, `STRATA_SPLIT26_FIXED_RESIDENCY=1`, `--layer-split 26`, and a valid `STRATA_SPLIT26_FIXED_MAP`.

**The fixed26 map is model/profile-specific and is not distributed here.** Runtime checks validate its geometry, membership and ordering. Do not substitute an arbitrary map or bypass those checks. Without the matching validated prerequisites, keep fixed26 disabled and retain the ordinary split path; that is not the measured full combination.

Checkpoint payload move is default OFF and was selected with:

```text
STRATA_CKPT_PARK_PAYLOAD_MOVE=1
STRATA_CKPT_POOL=0
STRATA_CKPT_THREADS=0
STRATA_SLOT_CKPT_MOVE=0
STRATA_PREFILL_PIPE=0
STRATA_RECOVERABLE_RESERVE_512=0
```

Turning payload move OFF selects the original copy path, but does not remove the unconditional exception-safety hardening. To recover an exact prior executable, use the preserved prior build rather than assuming one flag reconstructs it. Startup map/head audit selectors were enabled in the measured protocol; this is not a claim about an unmeasured audit-free variant.

The new adaptive-HC retry, unbuilt GEN bounds fix, worker-count experiments, and rejected micro-probes are not part of this integration. Checkpoint pooling was OFF; no new pool policy is enabled.

## Historical measured results

The October 23 qualification used six fresh processes per context: FOUR, prior combination, integrated, integrated, prior combination, FOUR. There were two observations per condition, mirrored ordering, exact generated IDs and unchanged logical cache/work admission. No outlier was dropped.

Integrated versus FOUR (positive rates are faster; negative latency is shorter):

| Context / phase | PP rate | TG rate | TTFT | Total wall |
|---|---:|---:|---:|---:|
| 64K input-cache-cold | +4.1035% | +1.7829% | -3.9423% | -3.6551% |
| 64K cached 1K output | +3.3441% | +2.2194% | -3.2377% | -2.2675% |
| 64K cached 4K output | +2.8122% | +2.0723% | -2.7494% | -2.0499% |
| 8K input-cache-cold | +1.9045% | +1.6820% | -1.8711% | -1.7743% |
| 8K cached 1K output | -0.0248% | +0.4940% | -0.0118% | -0.4452% |
| 8K cached 4K output | +0.4999% | +0.8387% | -0.5259% | -0.8228% |

 Cold  means input-cache-cold after shape warmups, not a cold server launch. Cached PP rates use actual newly read tokens, not the full context length. Both contexts together checked 73,752 generated IDs; STOP/distractor/restore added 4,132 IDs. Each native process retained all 24 graph shapes.

The user selected this as the next R&D reference despite mixed incremental results versus the prior combination. In particular, 8K incremental regressions remained in some PP/TG/TTFT/wall endpoints, and 64K incremental cached-4K PP/TTFT regressed slightly. Two observations per condition do not establish universal nonregression, rare-tail reliability, or a fix for historical stalls. A retained FOUR warmup outlier is not included in the C/D/E table above and was not removed from the historical results.

This document contains no private prompts, token lists, model/profile/map payloads, credentials or host paths. The optional private source inventory and raw evidence bundle are not published by this integration. The original FOUR rollback remains separate from the selected R&D baseline. Live service configuration is unchanged.
