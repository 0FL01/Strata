# Historical c183 empty-PCIe: reversed BAAB PP confirmation

## Decision and scope

**PASS_FIXED_C183_EMPTY_PCIE_BAAB_SCREEN_ONLY.** One reversed **B1, A1, A2, B2** confirmation on the unchanged c183 full-stack binary measured **51.4619554949 → 53.9035789540 TG tokens/s (+4.7445213375%)** with empty-PCIe skipping ON. Both TG pairs were positive, **+5.7597542954% / +3.7504412749%**. PP changed **646.5133111462 → 646.8580360573 tokens/s (+0.0533206208%)**, with both pairs positive, **+0.0131294225% / +0.0935561707%**.

The practical decision is to **retain empty-PCIe ON in the existing c183 best-known fixed profile at approximately 53.9 TG tokens/s** and end this specific PP-confirmation repeat sequence. This is an existing-binary confirmation, with no source patch, service promotion or new release-port qualification. **Zero PP loss and a universal output or quality guarantee remain unproven.**

The [original ABBA](../2026-10-11-gfx906-c183-empty-pcie-fixed/README.md) remains intact: TG **+1.8552228913%**, aggregate PP **−0.4304983802%**, and its first PP pair **−1.5124604459%**. That loss was not discarded or relabeled as noise.

## Same treatment and frozen rules

All four arms were cold native processes, each with one 65,536-token prompt and 1,024 outputs. A is `STRATA_VERIFY_SKIP_EMPTY_PCIE=0`, B is `1`; all other historical full-stack flags, the fixed policy (spec 6, MTP maximum 4, suffix draft 0), fixture, and compiled executable were unchanged. Historical `STRATA_EXP_MODE=16` is the expert GPU-kernel dispatch selector, not precision or bit width. The existing executable has 21,589,440 bytes and SHA-256 `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.

The before-data gate stayed unchanged: TG gain of arithmetic mean rates at least +1%, both TG pairs strictly positive, aggregate PP at least −1%, all historical IDs exact, and all available work equal. There is no individual PP-pair gate. Aggregate gain is `100*((B1_rate+B2_rate)/(A1_rate+A2_rate)-1)`; pairs are B1/A1 and B2/A2 regardless of execution order. All gates passed. There was no warmup, additional timing arm, outlier exclusion, time subtraction or threshold change.

## Complete BAAB measurements

| Arm, execution order | Empty-PCIe skip | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| B1 | ON | 101299.2 | 19014.7 | 646.9547637099 | 53.8530715709 |
| A1 | OFF | 101312.5 | 20109.9 | 646.8698334362 | 50.9201935365 |
| A2 | OFF | 101424.3 | 19690.9 | 646.1567888563 | 52.0037174532 |
| B2 | ON | 101329.5 | 18979.1 | 646.7613084048 | 53.9540863371 |

Rates are `65536*1000/prompt_ms` and `1024*1000/decode_ms`, from native prompt/decode counters; model loading and request-wall time are excluded.

All **4,096** BAAB historical output IDs match. Every arm has accepted/offered drafts **647/868**, cache hits/lookups **580670/598560**, prompt read/reused **65536/0**, and suffix draft 0. RAM/file blobs, offloaded experts and file-read MB are zero. Five optional chain/window counters are unavailable and remain null, so equality of available work does not establish equality of every unreported operation.

## All eight arms: descriptive context only

| Native-counter metric | OFF arithmetic mean, tokens/s | ON arithmetic mean, tokens/s | Change |
| --- | ---: | ---: | ---: |
| PP | 645.6164286772 | 644.4010375310 | −0.1882528220% |
| TG | 52.1947687213 | 53.9065427589 | +3.2795892760% |

These means include all four original ABBA and all four BAAB arms, with no exclusion or adjusted timing. They are **descriptive, not a new qualification**, and do not supersede either epoch's frozen rule. Available work matches across all eight arms.

The ON TG mean is almost unchanged between epochs: **53.9095065638 → 53.9035789540 (−0.0109954814%)**. The OFF mean falls **52.9275819477 → 51.4619554949 (−2.7691165908%)**. That slower OFF epoch drives the larger BAAB relative gain; **+4.7445% must not be treated as a stable effect size**. The original first PP-pair regression remains part of this descriptive pool.

## Frozen PP-chunk descriptor

Before BAAB data, the 16 same-ordinal median chunk increments of all four original ABBA arms were frozen as the reference. A descriptive large-delay flag means **new increment minus reference median strictly greater than 500 ms**. This is not a performance gate, an outlier-removal rule or a formal equivalence test. Native cumulative PP rows round to 1 ms; the half-ms reference medians are preserved.

| BAAB arm | Count >500 ms | Maximum positive residual, ms | Sum of positive residuals, ms | Last progress to prompt-end tail, ms |
| --- | ---: | ---: | ---: | ---: |
| B1 | 0 | 37.5 | 109.5 | 195.2 |
| A1 | 0 | 52.0 | 128.0 | 195.5 |
| A2 | 0 | 44.5 | 194.5 | 202.3 |
| B2 | 0 | 34.0 | 101.5 | 196.5 |

[Metrics](metrics.json) retain every original ABBA reference increment and every BAAB 16-point endpoint, cumulative-time, increment and residual curve, as well as the complete native prompt/decode times. No chunk or tail was removed or subtracted. Zero flags only says none of these BAAB chunks crossed this fixed descriptive threshold; it does not prove zero PP loss.

Retained-data diagnosis localizes **1,513 ms of the original B1−A1 1,555.8 ms PP penalty (97.2490%)** to interior chunks 4 and 10. The remaining chunks plus tail contribute 42.8 ms. Source inspection places the empty-PCIe knob read and graph capture after the PP cutoff. These observations narrow the investigation but do **not** prove noise, a thermal cause, or another causal explanation. Sparse GPU samples cannot reconstruct subsecond execution; PP-specific CPU wait-time data were not retained.

## Audit, cleanup and provenance

The independent actual-runtime audit passed **327 checks** and bound the four cold processes, actual OFF-0/ON-1 treatment, unchanged other historical flags, timing, all 4,096 IDs, available counters and cleanup. It performed no new GPU operation. One authorized BAAB launch completed all four arms; cleanup passed, the API remained stopped, and the maximum final sampled sensor was **55°C**. This sample is not continuous thermal proof.

The separate descriptor/pool independent review passed **48 checks**, recomputing the frozen reference, all BAAB chunk curves and the all-eight descriptive pool without any GPU operation. Its SHA-256 is `9822b29ce3a6043c500adf162d866b9427323006fb684f01e7d28bea9135b813`.

The frozen BAAB raw archive has **142,774 compressed bytes**, **64 regular files**, and **1,042,701 expanded bytes**. SHA-256 provenance:

- Raw archive: `4d64914370675865e2063962cdb9da9be317b93710ee695e8c98a0bf61d9ef29`.
- Native-rate analysis: `edfd440520871f8d12f01b941ad88be146d8a6ca74a007004a1af32f64660846`.
- Chunk and all-eight descriptive analysis: `501750e7d6db4b881b4ebc20dce7bf6ad12bae6b522a71ff7aea957038143c28`.
- Frozen before-BAAB chunk descriptor: `494ad5a28858b7c04a4bfef10afe64a355ad96beef8b2ef3a17915fbe3860c4c`.
- Actual-runtime independent review: `9d5ccc0bfab96f4fba1176decb661c31298a9a178d24e62a0cfca5b0ffddde7c`.
- Original ABBA analysis: `bd9f9e052c3922960f83fd913a65961f4f104ede902379f99a22eb655346416c`.

This documentation-only update changes no runtime source or deployment. Earlier failed gates, release-local experiments and adaptive-profile results remain separate. Public evidence consists of rates, native times, numeric chunk curves, available counters, counts, parity booleans and provenance hashes. Complete token-ID arrays, generated text, raw DONE payloads, raw logs, private paths, process identifiers and configuration contents are not published.
