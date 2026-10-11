# Release-local REG2/FIT17: unpruned fixed-policy screen

## Result and scope

**PASS for the new fixed-tail0 screen only.** Four cold 65,536-token / 1,024-output arms on the same retained release-local top-k executable measured **+2.8344133108% TG**, with both TG pairs positive. Mean PP changed **−0.1435327999%**; both PP pairs are negative. These PP results are visible and permitted by this epoch's before-data gate. The independent actual-raw audit passed **190 checks**, including all four complete output arrays against the historical 1,024-ID reference and equality of every available work field to fresh A1.

This is a new unpruned, suffix-disabled policy epoch. The [2026-10-10 default-tail7 adaptive top-k screen](../2026-10-10-gfx906-v0142-topk-stack/README.md) still **FAILS** its original strict nonnegative-companion-pair rule. That receipt and decision are unchanged. This result does not qualify the ordinary adaptive profile, promote a default/service, or establish a full-stack or cross-release gain.

| Native-counter metric | OFF mean, tokens/s | ON mean, tokens/s | Gain of mean rates | B1/A1, B2/A2 changes |
| --- | ---: | ---: | ---: | --- |
| PP | 626.2317902612 | 625.3329422390 | −0.1435327999% | −0.2553869493%, −0.0317202200% |
| TG | 48.1284354316 | 49.4925942118 | +2.8344133108% | +1.2242072933%, +4.4780544229% |

## Fixed method and predeclared decision rule

Order: **A1, B1, B2, A2**, one fresh cold native process and one complete request per arm. There were no warmups, GPU retries, rebuilds or additional diagnostic arms in this epoch. A selects `STRATA_GFX906_TOPK_REG=0` and `STRATA_GFX906_TOPK_FIT17=0`; B selects REG=2 and FIT17=1. This is the combined REG2/FIT17 treatment, not an attribution to either flag alone.

All arms reuse executable SHA-256 `cdf8dffcddc6bc6c84c03cb90567d9c1e71e687af46791f4e46d9d5e4f071185`. Query swizzle/reduce12 remain ON. Tail skipping is explicitly OFF (`STRATA_ROUTE_TAIL_SKIP=0`); policy is spec 6, MTP maximum 4, suffix draft 0, adapt-every 0 and prompt-cache 0. Deterministic sampling uses temperature 0, top-k 1, top-p 1, seed 12345. The retained build/component/source admissions are provenance, not newly rerun component work.

Before any data from this epoch, the rule was frozen as:

- Gain = `100*((B1_rate + B2_rate)/(A1_rate + A2_rate) - 1)`, the gain of arithmetic mean rates.
- TG gain at least **1%**, and both B1/A1 and B2/A2 TG changes strictly positive.
- PP gain at least **−1%**. There is **no individual PP-pair nonnegative requirement** in this new screen.
- All four historical output arrays must match exactly, and every available work field must match fresh A1. Historical work equality is not required.

Every condition passed. The aggregate is not the average of pairwise gains, pooled timing throughput, or a post-hoc relaxation of the prior experiment. One four-arm screen on one fixture does not establish significance or broad repeatability.

## Per-arm timing and work

| Arm | Selector | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | REG0/FIT0 | 104670.8 | 21060.0 | 626.1154018122 | 48.6229819563 |
| B1 | REG2/FIT1 | 104938.8 | 20805.3 | 624.5163847881 | 49.2182280477 |
| B2 | REG2/FIT1 | 104665.1 | 20575.9 | 626.1494996900 | 49.7669603760 |
| A2 | REG0/FIT0 | 104631.9 | 21497.3 | 626.3481787103 | 47.6338889070 |

PP is `65536*1000/prompt_ms`; TG is `1024*1000/decode_ms`. These native-counter rates exclude model loading and request-wall time.

All four arms have accepted/offered drafts **647/868**, cache hits/lookups **580670/598560**, prompt read/reused **65536/0**, and suffix windows/accepted/offered **0/0/0** with the suffix record absent. RAM/file blobs, offloaded experts and file-read MB are zero. Five unreported optional chain/window counters remain null. [Metrics](metrics.json) retain exact timings, counts, parity results and SHA-256 hashes of the original output-ID JSON artifacts. The complete arrays remain private; the 190-check independent actual-raw audit compared every ID.

Suffix timing feedback is disabled, but MTP proposal lengths remain probability-driven from 1 to 4. Work equality was checked, not assumed; aggregate equality does not prove equality of all unreported operations. Exact IDs are fixture-local evidence, not a general quality guarantee.

## Execution, provenance and limits

Actual execution: **2026-10-11 10:58:45.676030–11:09:18.489968 UTC**. All four native processes and the runner exited 0. The actual-raw audit bound the four fresh process identities, READY/DONE environment and affinity, the retained binary, actual selectors and fixed-policy arguments, raw decimal native times, complete raw IDs/work, terminal cleanup and unchanged device settings. Tail-OFF is established through the actual process environment plus source proof, not merely an absent log banner.

Cleanup passed; the API remained stopped. High mode and 190 W caps were unchanged. Final maximum sampled sensor temperature was **52°C** (edge readings 47/46°C); sampled readings are not continuous thermal proof. Collection encountered a network failure after packing, then resumed transfer of the same frozen archive. No GPU rerun, repacking, dropped arm or better-result retry occurred.

The archive has **139,566 compressed bytes**, **64 regular files**, and **1,012,817 expanded bytes**. Immutable SHA-256 pins:

- Raw archive: `4ba2393d6a3641a69aa10fa4dbf537a3739fc155d93740142bbe47776bb4bffe`.
- Analysis: `6aa9ef2628db0f9eb0316369c1f0906136e53441d2cd1389789e7b3699a15cec`.
- Extraction: `9de415a9668ad16beb7ccd2c62a101190d345dc7a36db99232afbcb11285fa0b`.
- Pre-execution review: `d5edc288210d776fbfca14f14ec63b5f429d52f5d9107739c856aadfe0294830`.
- Actual-raw independent audit, 190 checks: `1360af0eaf072097b895095c7abdbe71f1f39f630fda21b7ede7cca9a09cc586`.
- Source proof: `c41a830e571981fa591d55db6288e4440f9a5a6bdd2238c7fa3dbe94f45a5be6`.

Historical c183 remains a separate frozen integrated stack and epoch, with its [near-53.75 TG recovery observation](../2026-10-11-gfx906-c183-recovery-inclusion/README.md). Its timing cannot be compared as a controlled baseline here or reconstructed by summing component gains. The current release's tail-OFF/fixed-policy baseline is distinct. Historical model payloads still lack a complete independently verified hash inventory.

This publication adds documentation and sanitized numerical receipts only. No runtime source change, ordinary-profile qualification, full-stack result, 200K-prompt test, promotion or deployment follows. Output-ID arrays, generated text, private paths, process identifiers, configuration contents, raw logs and model payloads are excluded.

