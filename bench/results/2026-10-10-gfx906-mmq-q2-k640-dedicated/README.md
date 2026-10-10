# Dedicated Q2_0 K640 MMQ: resource and scheduling experiments

**PARK_NO_MODEL_QUALIFICATION.** This separate dedicated-entrypoint follow-on to the [earlier runtime-tail experiment](../2026-10-10-gfx906-mmq-q2-k640-tail/README.md) tested three versions. V1 parked before GPU testing at 104 allocated VGPRs. V2 reached 64 VGPRs/zero spills and exact semantic replay, but increased eligible-cell latency by **26.195647–27.955291%**. V3 restored the original dot schedule with literal stride ten, reached 80 VGPRs/zero spills and exact semantic replay, but **14 of 16 eligible timing cells missed the frozen 5% component threshold**. Core savings were only **3.594554–4.471563%**, also below the separate 12% campaign threshold. No model build, model-throughput claim, promotion or deployment follows.

## Dedicated entrypoint and scope

The prior runtime-tail version modified the existing J32 kernel, including its compiled behavior on ineligible K values. This experiment instead adds one separately named Q2_0/J32/nonfallback kernel and one descriptor while preserving the original supported kernels. A separate helper executes a two-iteration populated prefix, then a peeled final populated half and the exact ordered scale-only padded half. The prefix is a loop; actual v1 ISA shows it was not unrolled. There is no runtime K/tail-choice branch in the dedicated tail.

Host routing is restricted to gfx906, Q2_0, J32, nonfallback, non-stream-K, actual K640, M2560, row stride ten Q2 blocks, and non-null MoE IDs/expert bounds. Existing J/fallback selection remains authoritative. Other shapes and K values retain original symbols. Original K768 device code is byte/resource-identical; this does not prove zero host-dispatch or end-to-end overhead. The actual model's eligible launch histogram remains unknown.

The new entry preserves the original 24 explicit arguments and 172-byte extent, wave64, block(64,4), 24,000-byte dynamic LDS and zero static LDS. Ordered live-K accumulation, real neighboring-row scale loads/conversions and four scale-times-positive-zero/FMAC updates per output remain required. Zero integer dots do not permit deleting exceptional floating-point scale updates. Original allocation padding and final barrier remain part of the contract.

## Dedicated v1: compiled, resource gate failed

OFF object/module reproduction was exact. Both OFF and ON compiler invocations exited zero; the scope wrapper exited one. The new target was 9,980 bytes, with metadata VGPR count 102, allocated VGPRs 104, SGPRs 40 and zero private bytes/spills. The unchanged resource rule preferred <=80 allocated VGPRs, required reassessment at 81–96 and parked anything above 96. Therefore v1 was parked without GPU semantics or timing. Zero scratch does not override its resource failure.

The raw scope receipt remained failed. Independent comparison found 46 original functions byte-identical, 64 original descriptors unchanged except entry displacement, and 21 unsupported error stubs with changed PC-relative literals. Each stub was proved to call the same unchanged callee; this was a separate relocation explanation, not blanket byte normalization or rewriting the failed receipt. No original function was removed. This scope explanation did not override v1's resource PARK.

## Dedicated v2: two changes, lower registers

V2 exposed literal row stride ten to the dedicated loaders and changed only the dedicated dot helper to output-serial loop ordering. Each output retains its original four ordered K updates and original read-address multiset. The original dot helper and zero-tail helper remain unchanged. Both changes were made together, so a performance difference cannot isolate the effect of literal stride, serialization or register count.

Actual v2 resources were 12,184 code bytes, metadata VGPR count 63, allocated VGPRs 64, SGPRs 40, zero private memory and zero spills. Code remained below the 12-KiB gate. The same exact OFF reproduction and original-function/descriptor invariants passed, with the original failed raw scope receipt and separately proved 21 stub relocations preserved. A separate combined static admission followed source, ABI, host-dispatch and ISA checks. It compared 24,576 ordered FMAC updates, 8,192 scale-load/conversion/LDS chains and 1,015,040 symbolic instructions; all 32 tail MUL/FMAC pairs and FP modes were retained.

Output serialization can trade independent-output instruction overlap for smaller live operand groups and repeat X loads or loop overhead. These are plausible mechanisms, not measured attribution. Lower register allocation alone is not a speed result. With 24,000-byte LDS, the prior two-CTA-per-64-KiB-CU limit also remains; register counts alone do not prove an occupancy-driven explanation.

## V2 actual semantic replay

The new candidate passed the independently reviewed 28-case raw-bit suite on each gfx906 device, 140 launches per device. A0/B0/B1/A1 full output comparisons cover 10,536,732 valid output words per compared arm across devices. Repeats, cross-device output/quantizer equality, actual padded quantizer zeros, guard/padding checks and cleanup passed. Main half-scale fixtures cover 256 ordered pairs; the signed adjacent-scale extension covers 324. This finite set includes exceptional values but is not exhaustive over all possible inputs.

Direct symbol replay replicates the narrow host predicate; it does not execute the production host-wrapper integration. Read safety is statically derived for fixed geometry; write canaries do not detect all overreads. Input post-images were checked by the driver but unchanged copies were not independently retained. Sampled admission does not rule out all conceivable hidden consumers. Baseline parity does not establish mathematical accuracy of either kernel. The old runtime-tail semantic PASS was not substituted for this candidate's fresh PASS.

## V2 timing: stable measurements, failed performance gate

The fixed screen ran **2026-10-10 11:56:50.781694–11:57:09.824922 UTC**, separately on each gfx906 device. Each device completed 15,725 launches across the same five synthetic shapes and hot/rotate4 regimes as the prior screen: M2560/J32 with K640 core counts [32,25], sparse partial [25,1], full grouped sixteen times 32, multi-tile [65,33] conditional on cap32, and K768 [32,25] original-symbol control. These counts are not a captured model frequency distribution.

Each cell used eight warmups per arm/regime and 24 alternating AB/BA pairs of 32-launch batches. Hot uses one slot; rotate4 cycles four preallocated slots and does not guarantee cold cache. Quantization, allocation, transfers and logging are outside the kernel event interval; host argument/submission gaps can contribute. Sixteen empty-event calibrations per shape are retained without subtraction. Devices and regimes are kept separate.

Median paired latency **increase**, percent (positive means slower):

| Shape | GPU0 hot | GPU0 rotate4 | GPU1 hot | GPU1 rotate4 |
| --- | ---: | ---: | ---: | ---: |
| Core | 26.991474 | 27.195350 | 26.966298 | 27.181080 |
| Sparse partial | 27.346878 | 27.376487 | 27.205606 | 27.284817 |
| Full grouped | 26.609385 | 26.495640 | 26.281136 | 26.195647 |
| Multi-tile | 27.683837 | 27.955291 | 27.508698 | 27.774648 |
| K768 original-symbol control | 0.009810 | 0.009620 | 0.024641 | 0.019289 |

All 20 cells passed the unchanged stability and timer-validity gates: relative MAD <=3% per arm, even/odd order difference <=3%, every batch >=0.1 ms, positive calibration evidence and maximum calibration <=5% of the minimum batch. Nevertheless, all 16 eligible cells failed the required >=5% median saving and >=2% fixed 99% bootstrap lower endpoint. All four K768 controls passed their >=-2% median / >=-3% lower-endpoint tolerance. Their small apparent differences use the unchanged original device kernel; they are not evidence of an instruction change or measured host-wrapper overhead.

The separate campaign-priority rule additionally required core and full-grouped >=12% median saving and >=10% lower endpoint on both devices/regimes. V2 fails well before that margin. **PARK_NO_MODEL_QUALIFICATION**; no selective rerun or gate relaxation. Bootstrap intervals describe a fixed serial-sample screen, not model-performance confidence intervals. The report states increased latency, not an equal percentage loss in throughput.

Independent audit recomputed all 20 cells, compared 693,273,600 raw output bytes, hashed 478 runtime files and checked 166 admission events. Parity, routing, guards, quantizer padding and cleanup passed. Maximum observed temperature was 53 C, and high mode/190 W settings were unchanged. Exact batch arrays, calibrations, intervals and audit hashes are retained in metrics. This establishes a synthetic component regression for the two-factor v2 candidate; it does not measure model PP/TG or isolate either source change's causal contribution.

## Dedicated v3: literal-stride-only ablation

V3 retains v1's original dot-loop scheduling and changes only the two dedicated loader strides to literal ten. The host eligibility predicate, zero-tail helper, argument layout, original kernels and barriers remain unchanged. This is a new controlled source hypothesis; it does not rewrite v2's result.

Actual resources were **80 allocated VGPRs** (metadata 79), 40 SGPRs, zero private bytes/spills, 9,680 code bytes and unchanged 24,000-byte dynamic LDS. Exact OFF reproduction, 46 original function identities, 64 original descriptor identities apart from entry displacement, and the original K768 route were verified. The raw scope receipt again remains **FAILED_STOP_FOR_ANALYSIS**, with its 21 same-callee PC-relative stub differences separately proved. Compilation success, the raw scope failure, independent scope explanation and eventual admission are distinct records.

Independent source/ISA review verified 24,576 ordered FMAC updates, 8,192 real half-scale producer chains and 585,728 symbolic instructions. The prefix remains a two-iteration loop; the tail has no runtime K choice, preserves all 32 ordered MUL/FMAC pairs and the final barrier, and retains original FP modes.

V3 passed a fresh 28-case/140-launch-per-device semantic replay, including 10,536,732 valid output words per compared arm across both devices, exact cross-device output/quantizer equality and all route, padding, guard and cleanup checks. The unchanged host replay driver was reused with independently bound v3 module and admission hashes; old candidate results were not reused. As for v2, direct symbol replay does not execute production host-wrapper integration, the fixture set is finite, and write canaries are not a runtime overread detector.

### V3 timing: small savings, failed frozen gate

The separately reviewed fixed screen ran **2026-10-10 12:21:18.254614–12:21:36.584972 UTC**. It reused the unchanged timing driver with newly verified v3 module/admission bindings; no driver recompilation was needed. Shapes, slot regimes, fixed 24 AB/BA pairs of 32-launch batches, calibration and performance gates were unchanged from v2. Each device again completed 15,725 launches. Direct replay still does not measure production host-wrapper dispatch overhead.

Median paired latency **saving**, percent (positive means faster; unlike the v2 table above):

| Shape | GPU0 hot | GPU0 rotate4 | GPU1 hot | GPU1 rotate4 |
| --- | ---: | ---: | ---: | ---: |
| Core | 4.205775 | 3.594554 | 4.471563 | 3.682497 |
| Sparse partial | 4.224689 | 3.654520 | 4.285533 | 3.802990 |
| Full grouped | 3.805554 | 3.814177 | 3.857599 | 3.833571 |
| Multi-tile | 6.006545 | 3.973750 | 6.074899 | 4.004690 |
| K768 original-symbol control | -0.000003 | -0.019266 | 0.009796 | 0.000025 |

All 20 cells were stable and timer-valid, with all four original-K768 controls within the predeclared tolerance. Only multi-tile hot passed the component gate, on both devices (6.006545% and 6.074899%). The other 14 eligible cells missed 5%. Core and full-grouped results also missed the separate >=12% median / >=10% lower-endpoint campaign rule in both regimes/devices. Therefore **PARK_NO_MODEL_QUALIFICATION**, without selective reruns or a revised threshold.

Independent audit recomputed all statistics and verified full parity, route selection, guards, quantizer padding, driver-reuse provenance and cleanup. It compared 693,273,600 output bytes, hashed 478 runtime files and checked 160 admission events. Maximum observed temperature was 52 C; power mode/cap remained unchanged. Raw sample arrays, intervals and all control differences, including tiny negative savings, remain in metrics.

V2 and v3 each have their own paired comparison against the frozen baseline. They were separate runs, not a paired v2-versus-v3 trial. Likewise, the earlier runtime-tail core saving near 11% is historical context, not a contemporaneous head-to-head result. The resource counts and these timings do not isolate a causal register-count effect or prove which scheduling/loader difference explains the gap. No eligible model-frequency distribution, model-weighted savings or PP/TG extrapolation is established.

## Provenance and public scope

[metrics.json](metrics.json) preserves resource, scope, semantic and audit seals, plus all 40 v2/v3 timing cells with raw samples, calibration, intervals and unchanged gate definitions. The 478 timing-file counts describe runtime audit scope, not total archive membership. Stage-specific historical review decisions are retained as issued; later semantic/timing admission does not rewrite earlier failed raw scope receipts.

- V2 timing archive: 68,316,094 bytes, SHA-256 eb75f47ff407eeedd225b8eda5f5e844872bffc116421b4730ce60a4c157215f
- V3 timing archive: 68,316,510 bytes, SHA-256 553d8551eb047ef5ebadf13cfb71f6d5f159a7bf6f0b59e04307b543273b6e45
- V2 independent actual timing audit: 1a46abdabb5ecdb42a5d8a4c6891074142019c14883bd73aa0179fb7346d858a
- V3 independent actual timing audit: fe85db819212fc9d512cdc2d8e47e6b8c8990e44e502b538a7d84e3b775b2010

 Private host paths, credentials, model payloads and raw logs are excluded. Hashes identify retained private evidence, not a standalone public reproduction package. Only this report, numeric metrics and archive index are proposed for publication; runtime source, PR bodies, c183 model binary and stable ce deployment remain unchanged.
