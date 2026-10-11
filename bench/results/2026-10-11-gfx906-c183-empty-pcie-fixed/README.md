# Historical c183 empty-PCIe ablation: fixed-policy reference restored

## Result and scope

**PASS_FIXED_C183_EMPTY_PCIE_ABLATION_SCREEN_ONLY.** Four cold 65,536-token / 1,024-output arms on the existing c183 full-stack executable measured **52.9275819477 → 53.9095065638 TG tokens/s (+1.8552228913%)** when empty-PCIe skipping was enabled. Both TG pairs were positive.

**The first PP pair regressed −1.5124604459%.** The second PP pair improved +0.6587654292%; aggregate PP changed **−0.4304983802%** (644.7195462081 → 641.9440390047 tokens/s). The frozen rule required aggregate PP at least −1%, with **no individual PP-pair gate**. The first-pair regression is retained in full and the threshold has not been relaxed. Its cause is not established; it is not attributed to noise or to an isolated mechanism.

The ON arms measured **53.8805577480 / 53.9384553796 TG tokens/s**, re-establishing the frozen c183 approximately-54-TG reference under fixed policy. This is a direct ablation of an existing feature on the original integrated binary, **not a new optimization, new release-port result or promotion**. The [earlier c183 recovery observation](../2026-10-11-gfx906-c183-recovery-inclusion/README.md) used adaptive suffix work; its historical work-gate failure remains unchanged. Release-local studies and their gates remain separate.

| Native-counter metric | Empty-PCIe OFF mean, tokens/s | Empty-PCIe ON mean, tokens/s | Gain of mean rates | B1/A1, B2/A2 changes |
| --- | ---: | ---: | ---: | --- |
| PP | 644.7195462081 | 641.9440390047 | −0.4304983802% | **−1.5124604459%**, +0.6587654292% |
| TG | 52.9275819477 | 53.9095065638 | +1.8552228913% | +1.8726650881%, +1.8378053791% |

## Fixed treatment and decision rule

Order: **A1, B1, B2, A2**. Every arm is a fresh cold native process with one complete request. Only `STRATA_VERIFY_SKIP_EMPTY_PCIE` changes: A is `0`, B is `1`. The rest of the original c183 full stack remains unchanged. The existing 21,589,440-byte executable was reused without rebuilding; SHA-256 `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.

Shared fixed policy is spec 6, MTP maximum 4 and suffix draft 0, with historical `STRATA_EXP_MODE=16` (the expert GPU-kernel dispatch selector, not precision or bit width). This is one direct four-arm ABBA, with no warmup or extra timing arm.

The before-data rule was:

- Aggregate gain = `100*((B1_rate+B2_rate)/(A1_rate+A2_rate)-1)`, the gain of arithmetic mean rates.
- TG gain at least **+1%**, and both TG paired changes strictly positive.
- Aggregate PP gain at least **−1%**. There is no individual PP-pair gate.
- All 4,096 historical IDs exact, with equal available work across the four arms.

All conditions passed. No arm was dropped and no timing retry or threshold change follows. This single screen does not establish significance, broad repeatability or a general quality guarantee.

## Per-arm timing and parity

| Arm | Empty-PCIe skip | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | OFF | 101309.7 | 19360.9 | 646.8877116406 | 52.8901032493 |
| B1 | ON | 102865.5 | 19005.0 | 637.1037908725 | 53.8805577480 |
| B2 | ON | 101325.9 | 18984.6 | 646.7842871369 | 53.9384553796 |
| A2 | OFF | 101993.4 | 19333.5 | 642.5513807756 | 52.9650606460 |

PP is `65536*1000/prompt_ms`; TG is `1024*1000/decode_ms`. Native-counter rates exclude model loading and request-wall time.

All **4,096** compared historical output IDs match. Every arm has accepted/offered drafts **647/868** and cache hits/lookups **580670/598560**, with suffix draft 0. Prompt read/reused is 65536/0; RAM/file blobs, offloaded experts and file-read MB are zero. Five optional chain/window counters are unreported and remain null. Available aggregate counter equality does not establish equality of every unreported operation. [Metrics](metrics.json) publish rates, native times, counters, counts, parity booleans and provenance hashes; complete output arrays and generated text are excluded.

## Execution and provenance

One existing-binary experiment completed all four arms. Cleanup passed; the API remained stopped and the maximum final sampled sensor temperature was **55°C**. A sampled temperature is not continuous thermal proof.

The independent actual-runtime audit passed **327 checks**, binding the actual four-arm OFF-0/ON-1 treatment, unchanged other historical full-stack flags, all 4,096 historical IDs, available work, native timing and cleanup. It performed no new GPU operation. The screen outcome does not establish the cause of the first PP-pair regression.

The frozen raw archive has **143,542 compressed bytes**, **64 regular files** and **1,047,396 expanded bytes**. SHA-256 provenance:

- Raw archive: `0062b375b4fe656b8bddcf619a8e3892eafa8d7b814146444a88b67d86ee6e9f`.
- Analysis: `bd9f9e052c3922960f83fd913a65961f4f104ede902379f99a22eb655346416c`.
- Extraction: `4646638421d7c70c96bdd433398e07fdb71ef0c490dcc7f52db867d7c7e27235`.
- Actual-runtime independent review: `492611f5897e784639bb5b6c38a82c5628f9a7eeb15d12d1f3f138c6e9b3757b`.
- Pre-execution review: `784653e7fa7dafd91c2b3f2498f5f1186fcdd8fb386c094fed25b7749c6bb32c`.
- Source proof: `2d7dddab862b64198d716f0eaa04e6a75ee94a33c5d0403a15f3f8210f040c8e`.

This documentation-only archive update changes neither runtime sources nor deployment. No new optimization, ordinary adaptive-profile qualification, release-port model result or cross-release speed comparison is claimed. Gains are not pooled with or summed across other experiments. Private paths, process identifiers, complete raw payloads, logs, configuration contents, generated text and output-ID arrays are excluded.
