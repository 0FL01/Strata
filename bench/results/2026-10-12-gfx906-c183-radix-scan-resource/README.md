# PR #2016 cooperative radix scan: gfx906 resource rejection

**Park this candidate before GPU execution.** A narrow adaptation of [upstream PR #2016](https://github.com/Niko1221/Strata/pull/2016), pinned to `f6d8d7079fe0230e1616818a33313d5944d97dad`, replaces the radix scan only in the exact c183 guarded REG2/FIT17 arms and adds a nonpositive-width no-write guard. It is not a literal full upstream patch or a repeat of earlier radix variants.

CPU-side gfx906 compilation reports:

- **FIT17:** scratch **56→84 bytes/lane (+50%)**; VGPR spills **25→36**; SGPR spills **44→67**
- **Guarded REG66:** scratch **1,048→1,120 bytes/lane**; VGPR spills **468→500**; SGPR spills **539→549**

All six changes independently violate the unchanged no-regression resource policy. Allocated SGPR104/VGPR64, occupancy 4 waves/SIMD, LDS32,908 bytes, wave64 and 1,024 threads remain unchanged. These compiler resource counts are not measured runtime latency.

**Accounting correction:** the original gate mistakenly expected 13 kernels from a historical public harness. Production baseline and candidate both have 12; the absent historical symbol is `block_scores_simt_kernel`. All ten unaffected kernels match in bytes, complete metadata and remarks. The original failed receipt remains intact; this correction neither rewrites the gate nor removes its six resource failures.

Independent actual review verified **38 collected-file hashes** and bounded ISA observations of the uniform width guard/logical32 shuffle lowering; no full GPU correctness pass was issued.

Upstream's reported gfx1151/RTX3060 component benefits concern other hardware/compiler stacks and are not contradicted by this result. No GPU test, runtime correctness or speed measurement, model integration, rerun or variant sweep. [Aggregate metrics and provenance hashes](metrics.json).
