# QSA merge baseline exposure: parked before optimization

**PARK_WITHOUT_MODEL_QUALIFICATION.** The largest primary-device regime estimate is **821.6242314585002 ms**, below the predeclared **1003.739603960396 ms** screening threshold. This measures the unchanged baseline merge kernel on synthetic inputs. No candidate optimization, candidate speedup, model PP/TG result, rigorous bound or critical-path saving is established. No candidate, rerun, promotion or deployment follows.

## Completed baseline screen

The exact c183 module35 was loaded without compiling or changing device code. A separately compiled HIP host replay driver ran once on physical gfx906 GPU0, then GPU1, during **2026-10-10 07:40:39.968228–07:40:49.870794 UTC**. Both device runs and the wrapper exited zero; cleanup and all logged HIP return codes passed. The permanent one-use marker remains preserved. API and power settings were not changed; the API was left stopped. c183 is the combined R&D control, not a new stable deployment.

| Device and regime | Weighted median exposure, ms | Weighted sample minimum, ms | Weighted sample maximum, ms |
| --- | ---: | ---: | ---: |
| Primary GPU0, hot | 821.6242314585002 | 813.4700204557499 | 849.4709776072501 |
| Primary GPU0, rotate8 | 819.9847139062499 | 817.6780214572501 | 861.1256674275 |
| Peer GPU1, hot | 825.67162790175 | 818.4829556445 | 845.44955102025 |
| Peer GPU1, rotate8 | 824.626706697 | 823.2250858687499 | 864.02041468725 |

Only primary GPU0 sets the gate. Peer results are descriptive and are never added to primary exposure. Regimes remain separate; no best-cell combination is used. Weighted minima/maxima are descriptive sample ranges, not confidence intervals or bounds. The threshold is the predeclared optimistic +1% primary PP budget; the comparison is a prioritization screen, not a measured model improvement.

Each device completed **34 cells, 272 preflights, 476 timed samples, 4,624 total merge launches and seven empty-event calibrations**. Each cell has eight preflights, eight warmups per regime, then seven eight-launch timing batches per regime. Event intervals can include host dispatch/queue-starvation gaps. Empty-event calibration is retained without subtraction. Hot repeats buffer0; rotate8 cycles eight distinct buffers and does not guarantee cold cache.

## Conditional geometry and estimator

The dense-prefix reconstruction represents **65,535 queries in 2,048 batches per QSA layer**, with six main QSA layers per device in split27. It is not a captured per-head mask distribution. Cell0 has nb32/active33 and 1,983 calls per layer; cell1 has nb31/active33 and one call; the other 32 cells have nb32/active1..32 and two calls each. Grid is (24, nb, 1), block (256, 1, 1), with 33 chunks, 24 heads and 256 dimensions.

For each device and regime independently: sum over cells of **6 × calls per layer × median(seven batch times) / 8**. All raw printed sample times and float32 bit patterns are retained in [metrics.json](metrics.json), alongside the exact float32 recomputation from the independent audit. The tiny printed-decimal versus float32 rounding differences do not alter the gate.

Inputs and masks are deterministic synthetic buffers, not captured real partial accumulators. The driver checked numerical reference spots at documented tolerance 2e-6 + 2e-5 × abs(reference), every output for finite/written values, full repeated-output bit equality against each preflight, output tails/canaries and final input integrity. These are completed driver assertions, not independently exported numerical output arrays or model parity. The raw audit independently checked record counts, hashes, float bits, arithmetic and cleanup. Admission used stopped-container, known-process-name and sampled-idle checks; raw process lists and utilization admission snapshots were not retained, and absence of arbitrary hidden processes is not attested.

## Exact provenance and limits

- Baseline binary SHA-256: c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049
- Unchanged module35 SHA-256: 39694ccfe2d998208109f6e4a6a3f2b3a8e497d7d41293e2986d7e91a0668236
- Host driver SHA-256: 58ffa5e8a80b53dd80f870993704a028105bcad418e2fd079ba47dfda452c28a (31,160 bytes)
- Sealed package SHA-256: 47c7367d4b7cbed2dacc5126fa67f4151972c1ac86ee70b2f8933241400739d6
- Manifest SHA-256: 9b86c4e77385ce6177edc0f5a2d4062cd8653dc0106324476efb227e450eb4cb
- Raw receipt archive SHA-256: 0e5a5d8da84e5a8b11542053a897ac7451a4aefb17f48ba22b64be10c612417c (85,650 bytes)

Independent source/ABI/CPU and actual-receipt audits passed; exact hashes and scope-specific limitations are in the metrics. The current source reference is not proof of its historical compilation into c183; the extracted binary module is the device authority. No device kernel was rebuilt. Generic merge also serves verification, scalar decode and MTP; this screen covers only the stated PP geometry and establishes no TG safety. Mandatory accumulator loads and per-dimension FMAs would remain even if coefficient math disappeared.

The public derivative preserves numeric samples, geometry, regimes, calibration, thermal evidence, build/source/audit seals and the failed optimization-admission gate. Model payloads, output arrays, raw logs, host paths, pointers and credentials are excluded. Only this report, metrics and archive index change. Existing runtime sources, PRs and the stable deployment remain unchanged.
