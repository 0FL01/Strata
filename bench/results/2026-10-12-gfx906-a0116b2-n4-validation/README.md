# Fresh-main HC N4: correctness evidence, performance failure

**Performance qualification fails.** Fresh-main BAAB TG falls **0.138327%** (ratio **0.998616728 < 1.0**). A separate 4K correctness pair retains **−3.187818344% TG / +655.9 ms decode**. Neither is erased by later diagnostics.

Base: `a0116b2782a5b82622358c04a06496485d12b2d6`; experimental N4-only port, auxiliary placement OFF. This is separate from historical c183/affinity results.

- **Build and arithmetic:** 20 owner-0 finite fixtures / **327,640 FP32 elements** pass full-bit parity. Both-owner reference-preserving shadow passes **1,536 injections / 25,165,440 elements**. Final CMake-only relocation reproduces **131 objects, 245 compile-command rows, three binaries and the device image**; all **six official CPU CTests** pass. Fake-runtime tests and finite-corpus equality have bounded scope.
- **Eight-arm 64K/1,024 qualification:** ABBA PP/TG **+2.478767%/+0.016507%**; BAAB **+2.001407%/−0.138327%**. Frozen block gates require PP mean gain ≥1%, both PP pairs positive and mean TG ratio ≥1.0. All outputs/work/capacities match, but BAAB fails. Pooled **+2.240104%/−0.060944%** cannot rescue it.
- **Six-arm correctness:** all three full-output/work pairs pass. 4K retains the loss above; 200K TG is **−0.015582%** with 96 baseline tail fallbacks. True-default-OFF stock/candidate 4K/32 outputs match. Timing is descriptive.
- **One later 4K print-only diagnostic:** OFF is slower, decode **22,209.8→19,943.5 ms**. Outer verify changes **−2,265.48±3.48 ms** across 348 windows. This rounding-bounded aggregate cannot locate an owner, window or cause. The earlier ON slowdown did not recur; no fix or requalification follows.

Actual audits bind every stage; [metrics](metrics.json) retain all arms, means, pairs and hashes. Earlier [historical results and preservation](../2026-10-12-gfx906-c183-winner-preservation/README.md) remain unchanged. No qualified-speedup, universal-equivalence, default-promotion or ready-PR claim.
