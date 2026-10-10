# HIP blocking synchronization: exact outputs, failed performance gate

## Result

**Technical execution PASS; no performance qualification or promotion.** The frozen screen completed all seven arms with all 1,024 output token IDs and available work counters exact. Prefill throughput increased descriptively, but the companion token-generation (TG) nonregression condition failed. No threshold was relaxed and no rerun was used to select a win.

| Clean arm mean | PP tokens/s | TG tokens/s |
| --- | ---: | ---: |
| Frozen c183 (C) | 646.443930 | 53.865976 |
| Candidate runtime OFF (A) | 646.717281 | 53.813733 |
| Candidate runtime ON (B) | 655.022687 | 53.810340 |

| Contrast | PP change | PP forward/reverse pairs | TG change | TG forward/reverse pairs |
| --- | ---: | --- | ---: | --- |
| ON / OFF | +1.284241% | +1.290682%, +1.277798% | -0.006305% | +0.004730%, -0.017339% |
| ON / frozen | +1.327069% | +1.335467%, +1.318669% | -0.103285% | -0.143476%, -0.063052% |
| OFF / frozen | +0.042285% | +0.044215%, +0.040355% | -0.096986% | -0.148199%, -0.045720% |

These are descriptive measurements from two clean observations per arm, not a qualified end-to-end speedup. The PP candidate gate includes its TG companion condition, so its combined gate is false despite PP exceeding 1%.

## Frozen method and actual execution

The 65,536-token prompt / 1,024-token output screen used fixed seed 12345 and order **D0, C1, A1, B1, B2, A2, C2**. C was frozen c183; A and B used the same candidate binary with the runtime switch OFF and ON. D0 was an ON diagnostic with CPU sampling and was excluded from all performance comparisons. The gate required at least 1% PP or TG improvement in both ON/OFF and ON/frozen comparisons, positive forward/reverse pairs, and a nonregressive companion metric in the mean and both pairs of both comparisons.

Execution ran 2026-10-10 16:45:38–17:03:27 UTC. All seven arms passed output/work checks. Within each arm, all 28 persistent thread identities and READY/DONE affinity inventories matched. Original CPU placement and workload settings were retained. Peak sampled GPU sensor temperature was 82°C within the reviewed guards; final maximum was 51°C. Both devices remained in high mode with 190 W caps; owned cleanup passed and the API remained stopped.

## Source, failed baseline reproduction, and recovered build

The initial baseline reproduction failed exact object identity. Its source/header set did not reproduce the historical primary-commit ABI and scope code. That failure remains preserved; it was not relabelled as success. A separately reviewed reconstruction restored the historical generate, verifier, and IQ-kernel inputs while retaining the actual compatibility shim. V2 then reproduced exact c183, all 17 engine archive members, and all 55 device modules under the unchanged identity gates.

The candidate is a default-OFF host-side experiment, compiled with `STRATA_HIP_BLOCKING_INIT=1` and enabled only by `STRATA_HIP_BLOCKING_SYNC=1`. Compile-OFF reproduces exact c183. All 55 device modules remain identical in the candidate, and all 16 unrelated engine members remain unchanged. Runtime OFF performs no new HIP calls, supported by source/mock checks rather than inferred from missing logs.

The ON main hook initializes both devices before the first explicit runtime query and allocations/streams, checks calls and scheduling readbacks, and restores the original device. The peer path checks initialization and scheduling and bypasses its original Spin request. Actual ON records show old flag 1 on both devices, requests 4 and 12 (the latter includes peer MapHost bit 8), and scheduling readback 4 on both. Device restoration was checked. Returned nonscheduling bits were not required, so this does not assert a MapHost readback of 12. Static runtime initialization may precede main; accepted flags/readbacks alone do not prove interrupt-backed wait behavior. No mathematical, kernel, or workload-order change was introduced in the reviewed source delta.

## D0 CPU observation and limits

Across the same observed READY-to-DONE full request of **120.301574 seconds**, D0 recorded **23.11 main-thread CPU-seconds** and **472.09 process CPU-seconds**. Their difference is **448.98 CPU-seconds across other threads**. There were 24 diagnostic samples. These clocks cover PP plus TG and cannot be described as pure prefill. Other-thread CPU is not assigned to peer/backend roles or useful work.

There is no matched OFF CPU-telemetry control. Comparisons to earlier CPU diagnostics are unpaired and cannot quantify a causal CPU reduction, removable wait cost, or speed gain. The separate [CPU profile and selective offline unwind appendix](../2026-10-10-gfx906-prefill-cpu-profile/README.md) retain incomplete caller attribution and do not change this screen's failed qualification.

## Provenance and audit scope

The independent actual audit binds 80 raw files and separately recomputed paired metrics. Its initial environment check was corrected to compare the explicitly captured STRATA/HIP/ROCR/HSA prefix domain while retaining full manifest flags separately; raw evidence was unchanged. Private logs, paths, process/thread identifiers, and model payloads are omitted here. Full numeric results, source/build identities, preserved failure evidence, and receipt hashes are in [metrics.json](metrics.json).

- Actual audit SHA-256: `bc56a0355b02fc577f54e8e1dc7cc5697d5c88edac4e487f1d9761b9da211ecc`
- Recomputed metrics SHA-256: `b4d44a2b37d22bfe2e053d9114c0a59e9ef4ccee7fc056aa65380839636ba60b`
- Raw receipt archive: 248,455 bytes; SHA-256 `04ceb8b813a9c0f0b87431e95726f4f064d14f16a34b09b7126afe7baa96e761`
- Exact baseline reconstruction audit SHA-256: `3b1072162c3ba2bbbffdc0890deb09143b3bd7ecf506fd1705288c255c461976`
- Source review SHA-256: `87b6f7ec2a06a3acdcab5bf2386417cea9cb0d42c758019139a43489cffa0763`
- Actual build admission SHA-256: `7dea2bfef0fe94c78a724c49cb8a269261dcd3d379fe8ef173e5737e2588a235`
