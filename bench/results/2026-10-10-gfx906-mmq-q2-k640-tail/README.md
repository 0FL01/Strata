# Q2_0 K640 MMQ tail: parked after synthetic timing screen

**PARK_NO_MODEL_QUALIFICATION.** The candidate passed synthetic raw-bit replay and the isolated component timing gate on both gfx906 devices, but failed the separate frozen campaign-priority gate. Core median latency savings were **10.993426–11.033575%**, below the required 12% in every device/regime. The K768 negative control slowed by **0.226946–0.544809%**, within its predeclared tolerance. No model qualification, PP/TG gain, promotion or deployment is established. The combined c183 R&D control and stable ce deployment remain unchanged.

## Mechanism and scope

The frozen Q2_0 kernel executes 768 K positions for an actual K of 640; the final 128 activation positions are quantizer padding whose integer dots are zero. Those zero dots do **not** make the entire floating-point tail removable. Real adjacent-row weight scales remain live, and multiplying them by positive zero can matter for infinities, NaN payloads and signed-zero behavior.

The candidate is opt-in and restricted to gfx906, Q2_0, J32, nonfallback, actual K640 and the uniform final iteration. It preserves four ordered scale-multiply/FMAC updates per output, original weight loads, scale conversions and adjacent-row scale provenance. It removes the zero integer dots, corresponding Q8 loads and two intermediate barriers. The final barrier and all live-K accumulation remain. Other J, fallback, formats, architectures and actual K values are outside the optimized path. A partition ending at the same K-block index inside a larger actual K is not eligible.

Static arithmetic counts suggest 32 of 192 dot4 operations per output disappear, or 16.67%; including four zero integer-to-float conversions, 36 of 264 elementary arithmetic operations disappear, or 13.64%. These are instruction-accounting fractions, not latency fractions, speed predictions or bounds. Weight work, quantization, FP updates, writeback and launch costs remain.

## Preserved failures and static admission

The first macro-OFF full-object reproduction failed by 43 bytes after source insertion shifted diagnostic __LINE__ values by 52 lines. Numeric #line directives repaired this diagnostic-only mismatch without relaxing byte equality. Exact untouched-baseline and macro-OFF reproduction then passed. The original failure is retained.

Candidate v2 emitted 32 tail LDS scale reads and waits. Candidate v3 hoisted them to four reads and four waits while retaining all 32 MUL and 32 FMAC instructions in the inspected tail. Target code grew from 6,500 to 6,956 bytes; allocated VGPRs rose from 80 to 96, SGPRs remained 40, no scratch was introduced, and FP modes were unchanged. Dynamic LDS is 24,000 bytes, already limiting a 64-KiB CU to two CTAs. The extra registers consume headroom; these counts alone do not establish an isolated occupancy cliff or a performance outcome.

The raw compile scope receipt remains **FAILED_STOP_FOR_ANALYSIS**. Twenty-one unsupported error stubs had changed PC-relative literals. An independent per-stub relocation proof showed each still resolved to the same target: placement changed by +512 bytes and the literal by -512, with the other 44 bytes unchanged. A separate static admission passed for bounded correctness replay; the failed raw receipt was never rewritten. Static audit compared 24,576 ordered arithmetic updates and verified 16 scale-load/conversion/LDS producers per lane.

## Completed actual-GPU semantic replay

The reviewed replay ran during **2026-10-10 08:40:42–08:40:59 UTC**, separately on two physical gfx906 devices. Each completed 28 cases and 140 launches. The sequence was A0/B0/B1/A1 with full raw output words retained for independent comparison. Across both devices there were **10,536,732 valid output words per compared arm** (5,268,366 per device), with zero raw-bit mismatches, exact repeats and exact cross-device outputs and quantizer results.

The main suite covers 256 ordered half-scale pairs; a signed-NaN/adjacent-scale extension covers 324. This finite set of fixtures is not exhaustive over all half values or inputs. Actual quantizer padding zeros, negative dispatch cases, output guards, allocation padding, all 109 logged admission events and cleanup passed. The semantic audit hashed 572 files in the two GPU subtrees. The results subtree has 574 files after including its top-level admission and summary files; the complete archive has 581 regular files, all covered by the artifact hash map. Maximum observed temperature was 43 C. Baseline parity does not establish mathematical accuracy of either kernel.

Write canaries establish the checked writes, not absence of reads. Read safety is derived statically for the exact tested geometry, not demonstrated by a runtime overread detector. Input post-images were checked by the driver after each arm but were not retained separately when unchanged. Admission was sampled and excluded known process names; it does not attest absence of every conceivable hidden GPU consumer.

## Completed timing and separate campaign decision

The fixed screen ran **2026-10-10 08:56:09.311428–08:56:27.646028 UTC**. An independent actual-receipt audit passed and recomputed all statistics. Each device completed 15,725 kernel launches across five deterministic synthetic shapes and two regimes. M2560/I64/J32 nonfallback, non-stream-K geometry uses block(64,4) and 24,000-byte LDS. All shapes have K640 except the K768 negative control. Expert row counts are core [32,25], sparse partial [25,1], full grouped sixteen times 32, and multi-tile [65,33]. Multi-tile geometry is conditional on the archived cap32 dispatch; none of these counts is a measured model distribution.

Hot repeats one slot; rotate4 cycles four preallocated slots without promising cold cache. Each cell uses eight warmups per arm/regime followed by 24 alternating AB/BA pairs of 32-launch batches. HIP events enclose kernel submission only: allocation, quantization, transfers and logging are outside, but argument packing and host submission gaps can contribute. Sixteen empty-event calibration samples per shape are retained without subtraction. Devices and regimes are never pooled or added.

Median paired latency savings, percent (negative means slower):

| Shape | GPU0 hot | GPU0 rotate4 | GPU1 hot | GPU1 rotate4 |
| --- | ---: | ---: | ---: | ---: |
| Core | 10.995990 | 10.993426 | 10.996164 | 11.033575 |
| Sparse partial | 11.012191 | 11.188156 | 11.055098 | 11.170339 |
| Full grouped | 12.122278 | 12.118388 | 12.248617 | 12.250872 |
| Multi-tile | 11.598039 | 11.538169 | 11.632705 | 11.590450 |
| K768 negative control | -0.544809 | -0.288980 | -0.502392 | -0.226946 |

The **ISOLATED_SCREEN_PASS** required each eligible cell to save at least 5% at the paired median and at least 2% at the fixed 99% bootstrap lower endpoint. The negative control required median savings at least -2% and lower endpoint at least -3%. All cells also passed relative MAD <=3% for both arms, even/odd order difference <=3%, every batch >=0.1 ms, at least one positive calibration and maximum calibration <=5% of the minimum batch. These empirical timer checks are not a measured hardware timer-resolution guarantee. The bootstrap interval is a fixed serial-sample screening statistic, not confidence in a model-throughput gain.

The separate frozen campaign rule required both core and full-grouped shapes to save >=12% at the median and >=10% at the 99% lower endpoint on both devices and regimes. Full grouped reached 12.118388–12.250872%, but core missed 12% everywhere. Therefore **PARK_NO_MODEL_QUALIFICATION**. The gate was not relaxed after seeing the result; no selective rerun or retry occurred. Even a campaign pass would only have prompted a priority review of real coverage, not automatic model testing.

All before/after raw-bit parity, guard, quantizer-padding and suffix checks passed. The actual audit independently compared 693,273,600 raw output bytes, hashed 478 runtime files and checked all 157 logged admission events; the file count describes the audit scope, not total archive membership. Cross-device outputs and quantizer bytes matched. Maximum observed temperature was 51 C; high power mode and the 190 W cap were unchanged, and cleanup passed.

The small K768 slowdown is a measured regression within the control tolerance, not zero overhead. Exact sample arrays, calibration values, paired intervals and stability statistics for all 20 cells remain in metrics. No measured eligible-launch distribution or model-weighted saving follows. The broader profile down label includes activation quantization and ineligible work and cannot be assigned wholesale to this candidate. The earlier roughly 9.15% down-label context and the campaign margin are prioritization heuristics, not rigorous wall-time bounds.

## Provenance and public scope

[metrics.json](metrics.json) retains numerical case results, exact artifact hashes, resource counts and scope-specific limitations. The raw replay archive is 46,726,011 bytes, SHA-256 edc122e4f86819457e4e428db44172fa4af9a055193239aeae1aa4bba6a04987. The candidate ELF is bb250a2155162199a4f1e171f93920125b12648116efa8acc167d3814e888ab0; replay driver is 2739ea3f4e27d8a95effea1b53a01c1883b2184aaeded92d864ce4b6e59c7109.

The timing raw archive is 68,310,583 bytes, SHA-256 d5f8e8a91064b6b6fd8e8882cf2bd71b3a82e7a85fea69c46c3a856c0d825a26. Timing driver SHA-256 is 3b4d532d708b9ad9bad61708cbcb89ba28d510de45dfe18d323679bcc7246b36; independent actual-timing audit is d96bc3810b862785207c65b3488e5b2fcf95f9d29322b2e16eefbdc0376e56e5.

Only this report, numeric metrics and archive index are proposed for publication. Raw logs, filesystem paths, credentials, model payloads and binary output arrays are excluded. Hashes identify retained private evidence; they do not make that evidence public or provide a standalone reproduction package. No runtime source or existing PR changes are part of this archive.
