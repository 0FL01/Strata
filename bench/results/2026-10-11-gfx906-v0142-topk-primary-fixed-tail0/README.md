# Release-local primary overlap on REG2/FIT17: negative fixed-tail0 screen

## Result and scope

**FAIL_PRIMARY_OVERLAP_TG_MEAN_GATE.** Four cold 65,536-token / 1,024-output arms on the same new combined executable measured **+0.7383380771% TG**, below the predeclared **+1%** minimum. Both TG pairs were positive. Mean PP changed **−0.4848169684%**, within the predeclared −1% floor. All four complete output arrays matched the historical 1,024-ID reference, and every available work field matched fresh A1. The TG mean requirement is the only failed screen condition.

This rejects primary-overlap promotion for this fixed-policy screen. The separate [unpruned REG2/FIT17 screen](../2026-10-11-gfx906-v0142-topk-fixed-tail0/README.md) remains the retained screen winner. Its earlier same-binary selector comparison is not changed or pooled with this experiment. The [earlier default-profile primary-overlap failure](../2026-10-10-gfx906-v0142-primary-commit/README.md) also remains unchanged.

| Native-counter metric | Primary OFF mean, tokens/s | Primary ON mean, tokens/s | Gain of mean rates | B1/A1, B2/A2 changes |
| --- | ---: | ---: | ---: | --- |
| PP | 626.3628458645 | 623.3261325042 | −0.4848169684% | −0.9638337545%, −0.0058299397% |
| TG | 49.4991294718 | 49.8646003925 | +0.7383380771% | +0.2597852442%, +1.2099079386% |

## Fixed treatment and decision rule

Order: **A1, B1, B2, A2**, one fresh cold native process and one complete request per arm. REG2/FIT17 and query-swizzle/reduce12 remain ON in every arm. A leaves `STRATA_PRIMARY_COMMIT_OVERLAP` **unset**; B sets it to `1`. This flag is presence-based, so setting it to `0` would not represent OFF. `STRATA_COMMIT_SYNC` and diagnostic tracing remain unset.

All arms use new combined binary SHA-256 `3138b40bcedc0c53caceda53db943a71ee0ae75fe969fec52e89227f302dad9e` (**22,125,736 bytes**). This is an incremental same-binary primary-overlap comparison on an always-ON top-k stack, not a rerun of the selector treatment. Tail skipping is 0; policy is spec 6, MTP maximum 4, suffix draft 0, adapt-every 0 and prompt-cache 0. Sampling is temperature 0, top-k 1, top-p 1, seed 12345.

The before-data rule was:

- Aggregate gain = `100*((B1_rate+B2_rate)/(A1_rate+A2_rate)-1)`, the gain of arithmetic mean rates.
- TG gain **at least +1%** and both TG paired changes strictly positive.
- PP gain **at least −1%**; no individual PP-pair nonnegative requirement.
- Exact historical IDs for every arm, and equality of every available work field to fresh A1. Historical work equality is not a gate.

The rule was not changed after seeing the result. The first PP pair was −0.963834%; it is visible and does not independently fail this aggregate-PP rule. One four-arm screen does not establish statistical significance, broad repeatability or a general quality guarantee. No dropped arm, timing retry or threshold relaxation follows.

## Per-arm timing and parity

| Arm | Primary overlap | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | OFF | 104632.7 | 20840.4 | 626.3433897816 | 49.1353332949 |
| B1 | ON | 105651.0 | 20786.4 | 620.3064807716 | 49.2629796405 |
| B2 | ON | 104632.3 | 20290.8 | 626.3457842368 | 50.4662211446 |
| A2 | OFF | 104626.2 | 20536.3 | 626.3823019473 | 49.8629256487 |

PP is `65536*1000/prompt_ms`; TG is `1024*1000/decode_ms`. Native-counter rates exclude model loading and request-wall time.

Every arm has accepted/offered drafts **647/868**, cache hits/lookups **580670/598560**, prompt read/reused **65536/0**, and suffix windows/accepted/offered **0/0/0** with the suffix record absent. RAM/file blobs, offloaded experts and file-read MB are zero. Five optional chain/window counters were unreported and remain null. MTP proposal lengths remain probability-driven; available aggregate equality does not establish equality of every unreported operation.

All **4,096** compared IDs match the historical reference. Each original complete output-ID JSON artifact contains 1,024 IDs and is 5,430 bytes, with SHA-256 `333d09c6516beeb6ae8925cc0dec1959ad5a5555f196dec94c3be551ad24e17a`. [Metrics](metrics.json) publish timings, counts, parity booleans and whole-artifact hashes. Complete arrays and generated text are excluded.

## Execution and source provenance

Actual execution: **2026-10-11 12:14:23.112331–12:24:55.792290 UTC**. Four native processes completed and the runner exited 0. Two initial package-copy attempts failed on the network **before launch**; the third staging attempt launched the experiment once. These were delivery retries, not GPU or better-result retries. There were no warmups or extra diagnostic timing arms.

The new executable combines the exact six-file top-k/primary source union on release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`. The independent actual build review passed **89 checks**, binding source, compiler routes, object/archive hashes and actual link scripts. It is build provenance, not a new component or ISA-equivalence result. The top-k parity target remained disabled in the unchanged release build recipe. External libraries were image-bound, without an independently collected per-library hash inventory.

The independent actual-runtime audit passed **218 checks** while preserving the negative screen decision. It verified the actual four process bindings and completed requests, raw native times, all 4,096 historical IDs, available work equality, OFF-unset/ON-1 treatment, always-ON REG2/FIT17 with tail 0, and cleanup. The audit performed no new GPU operation. Primary environment and source/compile eligibility are bound with traces disabled; this is not a per-round activation-instrumentation claim.

Cleanup passed, and the API remained stopped. High mode and 190 W caps were unchanged; the final maximum sampled sensor temperature was **54°C**. Sampled temperatures are not continuous thermal proof.

The frozen raw archive has **140,370 compressed bytes**, **64 regular files** and **1,023,234 expanded bytes**. SHA-256 provenance:

- Raw archive: `342981b9688852962ad8ee12435445b7e00f92a7f3d64056bf877385225d9e99`.
- Analysis: `1602eac53060085afa68ebfc964c83d782f6770eae7cca1764d8485a122674f5`.
- Extraction: `15e7d629f92cbead80e4f4adf669fe6972132f16e3b629c2e90540066a19f0d3`.
- Pre-execution review: `3a81169a6447c074cc75b7510114453db3f2d5aa0ba1a76c6588ad0b9f874d33`.
- Actual build independent review: `d95bb56682fe59dc3887906fb3fbe5a5d6c570fe492053e0c35e8b1cc048afaf`.
- Actual-runtime independent review: `1a7d2e9f656510830fcd5b3a7f63c2cb8b8318ff488acdd0ea30abea7a515f1e`.
- Source proof: `6ab1eab4d7c3ee245edacece5061ea2f8fe19c84840afa615ee1d2469e36d424`.

The historical c183 integrated stack and its near-53.75 TG observation remain a different stack and epoch. Gains are not summed across experiments. This report makes no ordinary-profile, full-stack, cross-release, 200K capacity or public-port model claim. Historical model payloads still lack a complete independently verified hash inventory.

This archive update adds only documentation and sanitized numerical receipts. No runtime source change, promotion or deployment follows. Private paths, process identifiers, full raw payloads, logs, configuration contents, generated text and output-ID arrays are excluded.
