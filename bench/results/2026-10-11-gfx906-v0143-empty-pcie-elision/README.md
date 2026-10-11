# v0.1.43 standalone empty-PCIe elision: failed fixed-tail0 screen

## Result

**FAIL_V0143_EMPTY_PCIE_TG_MEAN_AND_PAIR_GATES.** Four cold same-binary 65,536-token / 1,024-output ABBA arms measured **48.470716 → 47.980444 TG tokens/s (−1.011480%)**. The first TG pair improved **+2.011688%**; the second regressed **−4.026131%**. Both frozen TG requirements failed: mean gain at least +1%, and both pairs positive.

PP mean changed **−0.227564%**, within the frozen −1% floor. PP pairs were **+0.072711% / −0.527503%**. All **4,096** output IDs, available work and stable INFO matched fresh A1. The independent actual-runtime audit passed **288 checks**, while preserving the failed performance decision.

| Metric | Elision OFF mean, tokens/s | Elision ON mean, tokens/s | Gain of mean rates | B1/A1, B2/A2 changes |
| --- | ---: | ---: | ---: | --- |
| PP | 626.0692424862 | 624.6445356486 | −0.2275637806% | +0.0727109429%, −0.5275027858% |
| TG | 48.4707158631 | 47.9804443345 | −1.0114798593% | +2.0116882365%, **−4.0261311836%** |

This is a failed performance screen, not a promoted optimization. Broader v0.1.43 prompt qualification remains pending. No upstream PR or deployment is made by this report.

## Pinned treatment and frozen gate

This experiment uses a **standalone five-file empty-PCIe elision port** on pinned upstream v0.1.43 commit `7695859aa13afb248bdb4d36f9b2e95707db079d`. It does not include the separate REG2/FIT17 or primary-overlap patches. Every arm uses executable SHA-256 `31e5603bc459c4a58554e17e5386b0e6528cf4b0b1aa45805a432721461693a5`.

Order is **A1, B1, B2, A2**, with one fresh cold native process and one complete request per arm on two gfx906 MI50 GPUs. The sole treatment is `STRATA_VERIFY_SKIP_EMPTY_PCIE=0` in A versus `1` in B. Tail skipping is 0; policy is spec 6, MTP maximum 4 and suffix draft 0.

The before-data gate was:

- Gain = `100*(mean(B rates)/mean(A rates)-1)`, using arithmetic mean rates.
- TG mean gain at least **+1%**, and both TG pairs strictly positive.
- PP mean gain at least **−1%**; no individual PP-pair gate.
- Every output ID, available work field and stable INFO field equal fresh A1.

Historical parity and historical work equality were descriptive, not admission gates. The thresholds remain unchanged. All four arms are retained without outlier removal, timing subtraction or a rerun-to-win.

## Native timings and work

| Arm | Elision | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | OFF | 104737.1 | 21156.0 | 625.7190622998 | 48.4023444886 |
| B1 | ON | 104661.0 | 20738.8 | 626.1740285302 | 49.3760487588 |
| B2 | ON | 105174.8 | 21981.4 | 623.1150427669 | 46.5848399101 |
| A2 | OFF | 104620.0 | 21096.4 | 626.4194226725 | 48.5390872376 |

PP is `65536*1000/prompt_ms`; TG is `1024*1000/decode_ms`. These native-counter rates exclude model loading and request-wall time.

Every arm reports accepted/offered drafts **647/868**, cache hits/lookups **580670/598560**, and prompt read/reused **65536/0**. Suffix-draft records are absent, with suffix windows/accepted/offered **0/0/0**. RAM/file blobs, offloaded experts and file-read MB are zero. Five optional chain/window counters remain unreported and null; equality of reported fields does not prove equality of every unreported operation.

All four original output-ID JSON artifacts are **5,430 bytes**, each containing 1,024 IDs, with SHA-256 `333d09c6516beeb6ae8925cc0dec1959ad5a5555f196dec94c3be551ad24e17a`. The [metrics](metrics.json) publish aggregate counts, parity results and hashes, not arrays or generated text.

## Unresolved B2 slowdown and PP localization

B2 decode took **21,981.4 ms**, versus **20,738.8 ms** in B1, a difference of **+1,242.6 ms**. The cause is unresolved. The two same-treatment observations are descriptive; their difference is not a controlled attribution.

B2 prompt time exceeded matched A2 by **554.8 ms**. The thirteenth 4K progress interval was **7,167 ms in B2 versus 6,597 ms in A2**, a **+570 ms** difference. All other intervals plus the tail net to **−15.2 ms**. The numerical 16-interval cumulative and incremental curves are retained in the metrics.

This localizes elapsed PP time only. It does not explain the decode regression or prove the interval is an invalid sample. Only **four approximate in-decode GPU samples per arm** were available; there are no retained per-token/verify timestamps, CPU scheduling/page-fault/I/O trace or GPU timeline. The sparse samples do not establish noise, thermal behavior or any other cause and do not justify excluding B2. Every original timing and pair remains in the failed screen.

## Historical reference labels and the retained v0.1.42 result

Every arm descriptively matches all 1,024 IDs in the historical c183 full-stack reference. Every arm differs from the **original v0.1.42 effective-tail7 B1 reference** at **999 positions**, beginning at zero-based index **13**.

That original effective-tail7 reference is **not** the later [qualified v0.1.42 tail0 REG2/FIT17 plus empty-PCIe winner](../2026-10-11-gfx906-v0142-topk-empty-pcie/README.md). The qualified tail0 report, its +1.760725% incremental TG screen and its separate 4K/200K correctness extension remain unchanged. It is a different binary, stack and epoch. This failed standalone v0.1.43 screen is not a controlled cross-version performance comparison or a revocation of that prior result. Gains are not pooled or summed.

## Separate component and guard validation

The two-owner component review passed. **Each owner** covered **120 zero-group cases, 20 nonempty-group controls, 200 state-transition sequences and 600 captured-graph replays**, with full in-memory byte comparisons and canaries. Component review SHA-256: `61d7f60d45eceec09d4581b009e4edd9ddd5c56a6fa7cda470dae0b820c2f009`.

The separate model guard review passed **386 output-ID comparisons**. Guard review SHA-256: `7c09b91c1c965327062ad9ec483e339f8d5c11dc9b6b644ce2175f4098791080`.

These technical results do not override either failed TG condition and do not establish broader prompt qualification.

## Actual audit, cleanup and provenance

The independent actual-runtime review passed **288 checks**, binding actual execution to the frozen candidate, source/treatment, complete requests and fresh-A1 parity/work/INFO. It recomputed the rates, pairs and failed gate and verified cleanup. The audit used retained evidence without new target operations.

Cleanup passed, the API remained stopped and the final maximum sampled sensor temperature was **53°C**. Final samples are not continuous thermal proof.

The private raw archive contains **246,248 compressed bytes**, **73 regular files** and **1,660,433 expanded bytes**. SHA-256 provenance:

- Raw archive: `5cc67837d6d714a3b5b80981ab33ea770bf1a5a1632845ad564a6a077d9cc288`.
- Analysis: `8e236fd730110deccc5b551ae85fdeb60cf061622492d20bed5d9d571b5fdb72`.
- Independent actual-runtime review: `de5468d621a2384cb9aeaf4c6e5dc51af197b788d82b1901af95b5b7018db204`.
- Build review: `94fef38392b2aceb0efef2fc0814d986d2faac61a9340db6fed8d4332fc78bae`.
- Source proof: `dd1055345afb6a0876d15d5ddd794e97fd167ef81675f172531f640fbb926492`.
- Runtime manifest: `4e48492e085d9f3e38261b491ffb8df5e208bf97ece286a446ca33ec1e3597b1`.

One four-arm screen does not establish statistical significance, broad repeatability or universal equivalence. Broader v0.1.43 prompt qualification remains pending; the v0.1.42 qualification is a separate completed result.

This publication adds only this report, sanitized numerical metrics and one index entry. Private paths, process identifiers, credentials, configuration contents, raw logs, whole raw receipts, model payloads, generated text and output-ID arrays are excluded. There is no production promotion or upstream PR submission.


## Follow-on decode diagnostic: prior slowdown not reproduced

**Diagnostic-only PASS; the failed ABBA above is unchanged.** One predeclared same-binary **OFF → ON** pair added only `STRATA_DECODE_TIMING=1`. Exactly two fresh 64K/1,024 arms completed, with all **2,048 output IDs**, available work and stable INFO equal. Reported work also matches the failed ABBA's fresh A1. The independent actual-runtime review passed **237 checks**.

Each arm recorded **379 actual verify windows**, **1,247 total verified T**, **1,024 emitted outputs**, **647 accepted drafts** and **868 offered drafts**. Reconstructed bucket totals use the printed **379-window** denominator. It must not be replaced by `1024−647=377`: the final window truncates two outputs. Per-output and per-accepted-draft normalizations use 1,024 and 647 respectively and are retained in the metrics.

Decode wall time was **21,110.2 → 20,744.0 ms (−366.2 ms)**. This single instrumented pair is not a speed qualification.

| Aggregate bucket | Owner/scope | OFF ms/call | ON ms/call | Reconstructed ON−OFF request ms |
| --- | --- | ---: | ---: | ---: |
| Outer verify | Host interval across the full verify call | 50.03 | 49.07 | −363.84 |
| GPU-reach wait | Primary verifier | 23.32 | 22.83 | −185.71 |
| Per-layer host | Primary verifier | 2.61 | 2.59 | −7.58 |
| CPU | Shared Drive across both owners | 2.61 | 2.58 | −11.37 |
| Draft | Outer serial-decode host interval | 4.52 | 4.51 | −3.79 |

Plan, actq, jobs, stage and commit/emit were unchanged at the printed precision. Each reconstructed bucket total has rounding uncertainty **±1.895 ms**; each OFF/ON bucket delta has **±3.79 ms** uncertainty. None of the absolute bucket shifts reaches the frozen **620 ms localization descriptor**, including its rounding bound. That descriptor is not a performance gate.

**Do not sum these buckets.** The outer host interval, primary-verifier wait/pool/host/stage measurements and both-owner shared-Drive counters overlap and have different scopes. The final aggregate snapshot follows the ordinary commit drain, **after the decode wall-time cutoff**. It is neither pure GPU timing nor per-round attribution.

The historical B2 slowdown **did not recur** in this pair. A persistent large host/CPU overhead is not supported by this observation, but the historical cause remains unresolved. The diagnostic cannot explain the old delay, justify an exclusion or overturn either failed TG condition. All original ABBA timings and conclusions above, and the separate qualified v0.1.42 result, remain unchanged.

Cleanup passed, the API stayed stopped and the final sampled maximum was **53°C**. The private diagnostic archive contains **155,351 compressed bytes**, **41 regular files** and **981,723 expanded bytes**. SHA-256 provenance:

- Diagnostic archive: `920ad69c369036a79252a360d7c2e0ce8b815cb599f82e9b133a3be95c846ebb`.
- Diagnostic analysis: `30c44ddd10beb6701bd238e8722c6df24ee5d8efc5b4d92787cdd5972930a74b`.
- Independent actual-runtime review: `ab8c8e4afc58636c0a9d86416799a3c53c1ce043e19db12bbf035afc55139115`.

The completed actual review supersedes the earlier analysis's pending-review marker. This adds diagnostic evidence only, with no performance qualification, rerun-to-win, promotion or upstream PR.
