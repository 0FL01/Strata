# Historical c183 recovery and v0.1.42 inclusion audit

## Outcome

**Historical output reproduced; frozen work gate FAIL.** One cold 65,536-token / 1,024-output observation on the retained c183 executable measured **646.567331 PP / 53.748202 TG tokens/s**, and every output ID matched the historical reference. This is descriptive evidence that the old integrated stack still reaches approximately 54 TG on this workload. It is not a new equal-work qualification, paired speedup, release-integration result or promotion.

The original binary was reused without rebuilding. Native prompt/decode times were **101,359.9 / 19,051.8 ms**. Rates are tokens × 1,000 / native milliseconds; load and request-wall time are outside these rates. There was one fresh process, no warmup, no comparator and no retry.

| Available work | Historical reference | New observation |
| --- | ---: | ---: |
| Accepted drafts | 648 | 648 |
| Offered drafts | 872 | 874 |
| Cache hits | 582,049 | 582,988 |
| Lookups | 600,000 | 600,960 |
| Suffix windows / accepted / offered | 5 / 9 / 16 | 6 / 11 / 20 |

The runner preserved the result and raw outputs, then failed the unchanged available-work gate with `available historical work counters changed`; its completion flag remains false. Exact output equality does not imply equal work. The historical adaptive policy is timing-trained, and these aggregate counters do not isolate why the work changed. Optional unreported counters remain unavailable.

Independent actual-raw review passed **66 audit checks**, including full historical INFO, raw protocol/IDs/counters, executable/image and READY/DONE process binding, positive native termination, both retained live inspections, and cleanup. The audit pass does not turn the replay gate into a pass: native exit was **0**, runner exit **1**. API remained stopped; high mode / 190 W settings were unchanged and final maximum sampled temperature was **50°C**. Sampled telemetry is not continuous thermal proof.

## Historical winner and release baseline are different

The [historical direct combined ABBA](../2026-10-09-gfx906-direct-c183-vs-ce/README.md) is the evidence for the integrated c183 winner: **53.821370 versus 50.532092 TG** and **647.068551 versus 598.318774 PP**, against already optimized ce. All four full arrays and available aggregate counters matched in that study, with the documented adaptive-policy and one-ABBA limitations. Its gains were measured directly, not added from component percentages.

The [pristine v0.1.42 research baseline](../2026-10-10-gfx906-v0142-release-validation/README.md) is a separate engine and profile. Query swizzle/reduce12 ON measured **51.076789 TG / 626.247328 PP** in its release-local attention screen. These numbers are not a controlled cross-version speed comparison.

Source/build inspection of release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406` gives:

| Historical feature | Pristine v0.1.42 status | Evidence and qualification |
| --- | --- | --- |
| Guarded QSA query swizzle and reduce12 | Present; ON in the tested release profile | Device eligibility guards and actual compile/runtime bindings were checked. Host trace selections are not every-launch or per-physical-GPU counters. |
| Strict-input scaled HC FP16 with native fallback | Absent | Release source lacks the strict-HC entry point and activation/guard switches; legacy environment flags cannot restore missing code. |
| Grouped Q2 MMQ J32 override | Absent; basic native MMQ remains compiled | Release passes the original maximum-row value instead of the historical `min(max_rows, 32)` selection hint. In this gfx906 compatibility backend, CMake cache `PREFILL_MMQ=OFF` does not disable the separately compiled native MMQ route. |
| Primary-only commit overlap | Absent | The release's generic commit synchronization is not the historical two-GPU primary specialization. A separate release-local port exists. |
| Empty-PCIe grouped-call elision | Absent | The historical mode-16/cache patch and later mode-7 release reimplementation have distinct contracts. |
| REG2 and scalar FIT17 top-k | Absent | A separate release overlay contains them; it is not the pristine baseline. The FIT17 core and host guard were byte-identical across historical implementation, public port and release overlay. |
| Historical PR1525 dequantization | Exact compiled donor unresolved; partial functional overlap | Current Q8_0 vector stores are present. The historical seven-source integration receipt omits the dequant translation unit; a dirty comparison worktree does not prove the historical compiled implementation or its contribution. |

The missing features do not quantitatively explain the whole cross-version difference. The release's output trajectory, aggregate work and expert-dispatch behavior differ. Its accepted/offered drafts are **678/862**, versus historical **648/872**. The first output difference is at **zero-based index 13**. Release evidence shows default tail-skip 7 active; the feature's markers are absent from the bound historical source and executable. Tail-skip alone causing the divergence is unproven. Do not add archived gains or promise 54 TG for v0.1.42.

## FIT17 interpretation

[Historical FIT17 studies](../2026-10-09-gfx906-qsa-fit17/README.md) changed FIT17 alone while REG2 stayed enabled: **+1.413177% TG** with suffix drafting disabled, and **+1.299911% TG** under adaptive policy. The historical gate allowed PP down to −1%; the adaptive study disclosed second-pair work drift.

The later [release-local top-k screen](../2026-10-10-gfx906-v0142-topk-stack/README.md) changed **REG=0/FIT17=0 to REG=2/FIT17=1** on one candidate binary. It measured **+2.564108% TG**, but failed the stricter unchanged companion-PP gate because its first PP pair was **−0.053470%**. That failure remains a failure; it does not disprove the historical winner or mean that the measured release TG gain was zero. The release treatment combines REG2 and FIT17 and cannot attribute their individual contributions.

## Provenance and scope

- Historical engine SHA-256: `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.
- Pristine release engine SHA-256: `572c7fb33c95d8b5c16803a8550abeab13eeccb9314136ae101ce61ecd605171`.
- Recovery receipt archive SHA-256: `03b487409b615cccf123b8d74e14a63ed4ed96fab051d27abbca37d6ca509299`.
- Recovery analysis SHA-256: `caf110bba9ece00cd93789252014b996b238a24bd8ef8feb5b03ee8ab2a437c9`.
- Independent actual-raw audit SHA-256: `71a175c939574b23cbcb80b39fa6ab725b258ab6ec6abdcdd6d810781daaee17`.
- Inclusion audit SHA-256: `c84b00766549235b1675819bbb17721709e4cb9618935b365569d80fbdb55c50`.

[Metrics](metrics.json) retain exact rates, counters, identities and qualification limits. Historical model payloads lack a complete independently verified hash inventory. Frozen executable/profile/fixture binding and exact output checks narrow that uncertainty but do not erase it. A complete release-stack claim would require a separately reviewed build and fresh same-profile controls. This publication changes documentation only; it contains no raw logs, private filesystem paths, configuration contents or model payloads.

