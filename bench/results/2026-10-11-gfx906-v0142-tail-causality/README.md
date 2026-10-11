# Release tail-skip causality and historical adaptive-work correction

## Result

**Tail-OFF restored all 1,024 historical output IDs on this fixed greedy fixture.** The existing pristine v0.1.42 executable was reused without a rebuild, with query swizzle/reduce12 still ON and only `STRATA_ROUTE_TAIL_SKIP=0` added to the retained release profile. One cold 65,536-token / 32-output diagnostic first restored the entire historical prefix; a separate cold 65,536-token / 1,024-output diagnostic then restored the entire historical sequence.

Against retained release tail-7 output, the short diagnostic differs at 14 of 32 IDs and the full diagnostic at 999 of 1,024 IDs. Both first differ at zero-based index 13 (tail-OFF/historical ID 11168; retained-release ID 220). Actual-raw independent reviews passed **71 checks** for the short diagnostic and **69 checks** for the full one. The single-setting intervention, source/default proof and actual-process bindings strongly support tail skipping as the cause of this observed historical/release output divergence. One fixture does not establish universal numerical equivalence or a general quality guarantee.

This advances the earlier [recovery/inclusion report's](../2026-10-11-gfx906-c183-recovery-inclusion/README.md) unproven tail-causality status. Its historical c183 work-gate failure remains unchanged.

## Why tail skipping was active

The release default is conditional on `!defined(STRATA_USE_HIP)` plus runtime eligibility. The actual `generate.cpp` compile command defines `STRATA_HIP_GFX906=1` but not `STRATA_USE_HIP`; the gfx906 compatibility build therefore entered the default-capable branch. The retained release log explicitly reports default rank 7 and 9,931 skipped missed experts / 10,594 entries. This is evidence for this binary/profile, not a claim that every HIP build or every release invocation defaults to 7.

At threshold 7, the source skips a nonresident expert only when its best zero-based rank across the window is at least 7; resident experts are retained. The getter/setter uses a process-global atomic. The bound historical c183 source/executable lacks the feature.

For both new observations, READY/DONE immutable bindings verified the actual process environment value `0` on the exact retained release executable. Source semantics and process binding establish OFF; absence of the ON banner and positive skip summary is supporting evidence, not sufficient by itself. Arguments, deterministic sampling, cold prompt, thread identities/affinity, release INFO and all other recorded environment settings were checked against the frozen release reference.

## Timing and work remain descriptive

The full tail-OFF observation measured **626.242241 PP / 47.779468 TG tokens/s**, from native prompt/decode times **104,649.6 / 21,431.8 ms**. Rates exclude model-load and request-wall time. There is no same-period ABBA or equal-work performance qualification here.

| Available work | Historical reference | Retained release tail 7 | Release tail OFF |
| --- | ---: | ---: | ---: |
| Accepted drafts | 648 | 678 | 648 |
| Offered drafts | 872 | 862 | 873 |
| Cache hits | 582,049 | 548,429 | 582,512 |
| Lookups | 600,000 | 569,246 | 600,480 |
| Suffix windows / accepted / offered | 5 / 9 / 16 | 2 / 3 / 8 | 5 / 9 / 17 |

All prompts were fully read (65,536), with zero prompt reuse. Optional unreported chain/window counters remain null. Exact output equality is not equal work. The historical integrated c183 best-known stack remains frozen and separate, with the fresh recovery observation near **53.75 TG**; this release's unpruned baseline is a different engine/profile. These observations do not isolate a cross-version performance cause, qualify an optimization or justify adding historical component gains.

## Historical adaptive-work correction

The fresh c183 recovery tuple (drafts **648/874**, cache hits/lookups **582,988/600,960**, suffix **6/11/20**) exactly matches the earlier [FIT17 adaptive study's B2 observation](../2026-10-09-gfx906-qsa-fit17/README.md). It is a previously observed adaptive-work state, not evidence of a newly introduced work anomaly. The prior recovery gate compared with the frozen **648/872, 582,049/600,000, 5/9/16** reference and still **FAILS**; that receipt is not rewritten or reclassified.

The retained DraftPolicy source uses whole-round timing EMA and a 3% selection margin. A UBSan CPU probe of the actual retained methods changes lookup-T6 to MTP-T4 when only the T6 cost changes from 10 to 30 ms, with observed sizes/acceptance fixed. This proves source-level timing sensitivity, not the actual replay crossover: no per-round cost/threshold trace survives. The compiled historical generate.cpp hash is bound, while companion-policy evidence is retained-source/CPU proof, not a new linked-binary reconstruction. Timing adaptation is intended behavior, not an established bug. The historical adaptive FIT17 study allowed work changes and remains distinct from fixed-work qualification.

## Completion, provenance and limits

Both diagnostic native processes and runners exited 0. Full-run cleanup passed, API remained stopped, and reviewed high mode / 190 W settings were unchanged. Final full-run maximum sampled temperature was **51°C** (edge sensors 45/44°C); sampled readings are not continuous thermal proof.

The full receipt transfer encountered a network timeout. Collection resumed by transferring the same frozen archive only, with no workload rerun or repacking. Its **59,539-byte** archive contains **22 files / 397,552 expanded bytes**. The retained launch/once/terminal identities and raw-file hashes were independently checked. No outcome was dropped or rerun for a better result.

[Metrics](metrics.json) retain full output arrays, exact counters/rates, comparison details and these immutable SHA-256 pins:

- Release executable: `572c7fb33c95d8b5c16803a8550abeab13eeccb9314136ae101ce61ecd605171`.
- Source/default proof: `e3fb829ce9493d828d314ceef0b2ce0e98d72787df8e1049ef1b96e963b10c00`.
- Short raw archive: `92b4a913c94951156f327753901e2142e55a11640ff09c9976b9578d0df9a344`.
- Short analysis: `249fa698dd3aacaa8555e4e3c5c7134db15871e9f81366d259cf9725bf0cc276`.
- Short actual-raw audit: `e5d161db858297b6f8e1a2962865a1f852bab40ad13d58705a3d1d5c70b26448`.
- Full raw archive: `e85d663faa4052008c33e5d317a43636962653613f436e455f84ef86ae14c70f`.
- Full analysis: `14be999cd87e73a1a6581e21097ca4feb38435839f72a68b7b7b2c96601e08df`.
- Adaptive diagnosis: `1c4b9f971ff07b07ba12509bfe5e8848e7d666d94ab287c53e42a2fbb5824a58`.
- Actual-source CPU proof: `323715da6d3d299f8fbff2b880408b5edfea88993aa56a0bbb782709b3d110ba`.
- Full actual-raw audit: `c46e022e591e66968b5cbaf9e3017e66ff7bc22101ae95967bdc21a21b9259af`.

This is a documentation/numeric-receipt update only. No source change, rebuild, deployment, default-setting promotion, general-quality claim or new performance qualification follows from it. Private paths, process identifiers, configuration contents, raw logs and model payloads are excluded. Historical model payloads still lack a complete independently verified hash inventory; executable/profile/fixture binding and exact output checks narrow but do not remove that limitation.
