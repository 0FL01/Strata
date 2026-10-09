# gfx906 radix-stop: two compile-time resource-gate failures

Date: 2026-10-09 UTC. Status: **parked before GPU qualification**.

Both the original radix-stop candidate (v1) and its single targeted lower-live-state repair (v2) compiled for gfx906, then failed the unchanged resource gate. Each build wrapper exited 14 after compilation. No candidate GPU test ran, no GPU runtime was loaded, and no full engine was built. These are compiler-resource rejection results, not GPU correctness or performance failures. Neither candidate is promoted.

## Design and CPU evidence

The optimization tries to omit the fourth radix byte when the selected third-pass bucket contains exactly one positive-weight block. Under the existing valid-input contract, full blocks weigh four cells and there is at most one partial tail; positive bucket mass at most four establishes that singleton. Multiple positive blocks conservatively retain four passes. Partial output budgets, ascending IDs, lowest-index ties and zero-weight tails remain part of the exact-output contract.

V1 recovers the complete numeric threshold through a shared full-key writer/readback. V2 is the only repair attempted: it normalizes positive keys in place during the existing count scan, removing recovery state and shared full-key traffic. On stopping, its prefix threshold can differ numerically from the original full key. The proved property is identical greater/equal/less partition and selected IDs after normalization, not numeric threshold equality. The host opt-in branch is unchanged.

Independent CPU harnesses passed 361,968 exact-output cases for v1 and 362,107 for v2, including 139 additional partial-budget cases in v2. Each also checked 1,000,014 raw float encodings and passed an AddressSanitizer/UndefinedBehaviorSanitizer repeat. Separately, each extracted-source harness passed 3,136 adversarial cases and 100,014 float-key cases.

Both variants replayed all 16 actual captured 64K/200K rows on CPU with exact captured baseline IDs; 13 rows took the modeled three-pass path and three retained four passes. That count is neither a measured time fraction nor a speedup. CPU sequential models and source synchronization arguments do not qualify HIP lowering, hardware races, graph behavior or performance.

## Fixed gate and observed resources

The same checker requires all 13 old functions to retain exact machine bytes, complete metadata and compiler remarks; both variants passed that preservation check. New specializations must have no increase in scratch, either spill count, SGPRs or VGPRs, no occupancy loss, and unchanged LDS/wave/thread layout. No criterion was relaxed.

- PER=17: baseline/v1/v2 scratch is 56/56/56 bytes per lane; SGPR spills 44/44/44; VGPR spills 25/26/34.
- PER=66: scratch is 1048/1096/1096 bytes per lane; SGPR spills 539/539/529; VGPR spills 468/493/559.
- All compared specializations report SGPR/VGPR allocation 104/64, occupancy 4 waves/SIMD, LDS 32,908 bytes/block and wave size 64.

Thus v2's reduced PER=66 SGPR spill count does not compensate for its scratch and VGPR-spill regressions. Both variants fail the same three checks: PER=17 VGPR spills, PER=66 scratch and PER=66 VGPR spills.

## Provenance and stopping point

[Numeric metrics](metrics.json) retain full public-source, input-manifest, checker, build-receipt, resource-gate and CPU-evidence SHA-256 identities. Both exported archives were hash-verified before safe extraction; all 35 exported files per variant were verified against their output manifests.

Hardware exact-ID replay, GPU sanitizer/race checks, graph growth/restore checks, paired timing and model qualification are **NOT_RUN**. Completed manual ISA qualification is not claimed. The first failure remains preserved beside its one failed repair. This line is parked with no further variants.
