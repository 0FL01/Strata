# Release-local empty-PCIe elision on REG2/FIT17: fixed-tail0 screen

## Result and scope

**PASS_TOPK_EMPTY_PCIE_FIXED_TAIL0_SCREEN_ONLY.** Four cold 65,536-token / 1,024-output arms on the same combined executable measured **49.846425 → 50.724083 TG tokens/s (+1.760725%)**. Both TG pairs were positive. Mean PP changed **−0.536465%**, within the frozen −1% mean-rate floor. **Both PP pairs were negative, including B2/A2 at −1.064662%.** The rule has no individual PP-pair gate.

All **4,096** compared output IDs matched the historical reference, and every available work field matched fresh A1. The independent actual-runtime review passed **412 checks**. This establishes one fixed-policy screen pass, not production promotion, general correctness, zero PP loss or a near-54-TG release result. The separate current-stack **4K/1,024 and 200,000/256 correctness extension has now passed**, with all 2,560 historical IDs and paired available work exact, confirmed by a 316-check independent actual-runtime review. This correctness extension makes no new speed claim. No upstream PR is submitted by this archive.

| Native-counter metric | Elision OFF mean, tokens/s | Elision ON mean, tokens/s | Gain of mean rates | B1/A1, B2/A2 changes |
| --- | ---: | ---: | ---: | --- |
| PP | 626.1842119418 | 622.8249535523 | −0.5364648813% | −0.0081197908%, **−1.0646615745%** |
| TG | 49.8464249929 | 50.7240832491 | +1.7607245781% | +1.8113626342%, +1.7101170784% |

## Fixed treatment and decision rule

Order: **A1, B1, B2, A2**, one fresh cold native process and one complete request per arm on two gfx906 MI50 GPUs. All arms use combined executable SHA-256 `5271849848cc95951e834f4ce4b11b1a1a6d9d21b08e94ff32c7a7ba851c87be`, based on release source epoch `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`.

Only `STRATA_VERIFY_SKIP_EMPTY_PCIE` changes: A sets 0, B sets 1. REG2/FIT17, query swizzle and reduce12 remain ON. Tail skipping remains 0; fixed policy is spec 6, MTP maximum 4, suffix draft 0, adapt-every 0, prompt-cache 0 and PCIe fraction 0. Prefill chunks are 4,096 tokens. Primary overlap and diagnostic timing traces are absent.

The before-data gate was:

- Aggregate gain = `100*(mean(B rates)/mean(A rates)-1)`, the gain of arithmetic mean rates.
- TG gain at least **+1%**, with both TG paired changes strictly positive.
- PP gain at least **−1%**, with **no individual PP-pair gate**.
- Exact historical IDs in every arm, and equality of all available work fields to fresh A1.

All conditions passed unchanged. The second PP pair below −1% is retained and visible. There is no dropped arm, subtracted interval, outlier correction or post-data gate change.

The prior [unpruned REG2/FIT17 screen](../2026-10-11-gfx906-v0142-topk-fixed-tail0/README.md), [negative primary-overlap screen](../2026-10-11-gfx906-v0142-topk-primary-fixed-tail0/README.md), and [earlier default-profile empty-PCIe screen](../2026-10-11-gfx906-v0142-empty-pcie-elision/README.md) remain separate, with their original decisions unchanged. Their gains are not added to this result.

## Per-arm timing and equal-work checks

| Arm | Empty-PCIe elision | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | OFF | 104674.0 | 20549.3 | 626.0962607715 | 49.8313811176 |
| B1 | ON | 104682.5 | 20183.7 | 626.0454230650 | 50.7340081353 |
| B2 | ON | 105770.7 | 20191.6 | 619.6044840395 | 50.7141583629 |
| A2 | OFF | 104644.6 | 20536.9 | 626.2721631121 | 49.8614688682 |

PP is `65536*1000/prompt_ms`; TG is `1024*1000/decode_ms`. Native-counter rates exclude model loading and request-wall time.

Each arm reports accepted/offered drafts **647/868**, cache hits/lookups **580670/598560**, prompt read/reused **65536/0**, and no suffix-draft record, with suffix windows/accepted/offered **0/0/0**. RAM/file blobs, offloaded experts and file-read MB are zero. Five optional chain/window counters remain unreported and null. Available-counter equality is not proof of equality of every unreported operation.

Each original full output-ID JSON artifact contains 1,024 IDs, is **5,430 bytes**, and has SHA-256 `333d09c6516beeb6ae8925cc0dec1959ad5a5555f196dec94c3be551ad24e17a`. All four artifacts have identical bytes and match the historical reference. [Metrics](metrics.json) publish counts, parity booleans and the whole-artifact hash, without publishing the arrays or generated text.

## PP cost: localized elapsed time, unresolved cause

The B2/A2 total prompt-time difference is **+1,126.1 ms**. The third 4K progress interval is **7,175 ms in B2 versus 6,051 ms in A2**, a difference of **+1,124 ms**. All other intervals plus the final tail net to **+2.1 ms**.

This localizes the observed extra elapsed time; **the cause is unknown**. It does not establish that the interval is an invalid sample, attributable to elision, or removable overhead. All original timings and both PP pairs remain in the calculation.

The metrics retain the numerical 16-boundary cumulative and incremental PP curves for all four arms. The final progress boundary is 65,535 tokens; the remaining tail reconciles each curve to its native total prompt time. Numerical progress counts are not model token-ID payloads.

## Separate component and guard evidence

Component admission passed for **8 V1 processes plus 2 V2 processes**, bound by composite receipt SHA-256 `1648cc04c9c85d8e747f53628a3149d893bf2db6e7345e496bd4378f7c95947c`. The original V1 late-inspect transition failure remains disclosed and excluded from valid component admission. This is component evidence, not full-model throughput.

The separate actual guard review passed **386 output-ID comparisons**, confirmed capture/reuse for both owners, and confirmed expected positive-PCIe refusal before prefill or output. Guard review SHA-256 is `646adae73ad94a28d6ded8804b9a0222bf1532a49b06f63ee80c51ef72d30fca`. Guard instrumentation is separate from the four untraced timing arms.

## 4K/200K correctness extension

**PASS_TOPK_ELISION_CORRECTNESS_ACTUAL_AUDIT.** The same frozen combined executable completed four fresh processes in order **C4OFF, C4ON, C200OFF, C200ON**. The fixed policy remains the screen policy, including REG2/FIT17 ON and suffix 0. Each same-prompt pair changes only empty-PCIe elision OFF/ON.

| Fixture | Outputs per arm | Total historical IDs compared | Accepted/offered per arm | Cache hits/lookups per arm | Historical IDs and paired work |
| --- | ---: | ---: | --- | --- | --- |
| 4,096 prompt tokens | 1,024 | 2,048 | 684/850 | 529826/571200 | Exact |
| 200,000 prompt tokens | 256 | 512 | 161/220 | 147072/151680 | Exact |

All **2,560** historical IDs matched. Outputs and all available work fields match within each fresh OFF/ON pair; equality to historical work counters is not required. Both fixtures have prompt reuse 0, no suffix-draft record, suffix windows/accepted/offered 0/0/0, and zero RAM/file blobs, offloaded experts and file-read MB.

These are correctness/capacity checks, **not balanced performance comparisons**. No speed estimate is taken from them. Selector branch/fallback coverage is source-inferred, without new device-counter instrumentation; this does not prove universal equivalence.

### Exact fixture recovery

The 4K fixture JSON SHA-256 is `6709011b1777b4b847dff88d3eab088d166f763c478f35c2eb42edb6bca4b058`. The historical 200,000-token fixture JSON SHA-256 is `736636e97ede94cc37e32447eefde4217a38bd17c81a7349345be98060e766c4`.

The original historical 200K target artifacts were absent. The exact historical bytes were recovered by repeating the retained 65,536-token prompt four times, taking the first 200,000 entries and serializing with Python `json.dumps` defaults, with no trailing newline. The resulting SHA-256 matched the historical fixture exactly. **No alternate-fixture fallback was used.** Prompt arrays and private locations are not published.

### Independent review and cleanup

The later independent actual-runtime review passed **316 checks**, binding this extension to the same candidate and prior guard/timing evidence, verifying all historical IDs, paired work, immutable execution identities and cleanup. This completed review supersedes the earlier analysis artifact's pending-review marker.

Cleanup passed, the API remained stopped and the extension's final maximum sampled sensor temperature was **54°C**. This is separate from the 64K screen's 53°C final sample. No production promotion or upstream PR follows.

The correctness raw archive contains **154,187 compressed bytes**, **72 regular files** and **1,292,358 expanded bytes**. SHA-256 provenance:

- Correctness raw archive: `ad275f5735ee27938d3837bfb4d8dc8f82a87c6f8057e4c36293ca691ef7df76`.
- Correctness analysis: `1642ca91f626751c1a613766d7074d140227b8b50aaecdb0e0b4b1776cec0dc0`.
- Independent correctness review: `1ff728db82541c51f3d73c23cdc47b3f49050b41da1db5c3ab88878b5e3dc6ef`.
- Correctness reference receipt: `13b8fd8b67d24cc65a027c990281f8d19696d0b77a72a75316638a438737fb9d`.

The original 64K rates, pairs, gates, numerical PP curves and unresolved PP cause above are unchanged. This extension qualifies only these fixtures on the frozen executable, not a different source port.

## Audit, cleanup and provenance

The independent actual-runtime audit passed **412 checks**. It binds the four actual process/request identities to the frozen candidate, verifies the sole elision 0/1 treatment and fixed policy, recomputes native rates and the unchanged gate, compares every historical ID and available work field, reconciles PP progress curves, and verifies cleanup. The review used the frozen evidence; it did not create new GPU performance observations.

Cleanup passed, the API remained stopped, and the final maximum sampled sensor temperature was **53°C**. Final samples do not constitute continuous thermal proof.

The raw archive contains **241,508 compressed bytes**, **73 regular files** and **1,650,039 expanded bytes**. It remains private. SHA-256 provenance:

- Raw archive: `8c1f052d37ebf6c4259545db0735253b68a19050431551ac0b71cd4b87781444`.
- Analysis: `032e72264169c7ce9953b7d1c0cfea1b07de4064e175e53c0d15009e14e03a94`.
- Independent actual-runtime review: `62989d2d5d53fb821e22db233c4159e74b6ff0ade360d9e62afd59f40fb3f6e2`.
- Extraction receipt: `eb5629d2e73b82bd194f16c2eb06deea8bd24da65b7b4e845206f400dcc56975`.
- Runtime manifest: `972d2d81819600cef6ccf5ecb059cd9703b60d3e69e0aabc5584bfd374098424`.
- Pre-execution review: `61317d7a7ed95d1e900cdf6e0e39de9b2f68acccda562abe1ce221cb4fb5ea8f`.
- Build review: `5411a9fc36902802d7a9aae58f344c82f5239a9734dffbe711694611f96eb585`.

One four-arm screen does not establish statistical significance or broad repeatability. Historical c183 measurements, earlier release screens and this current combined executable are distinct experiments; no cross-release or summed full-stack gain is claimed. The separate 4K/200K extension establishes correctness on the two checked fixtures, without establishing universal equivalence or adding performance evidence.

This publication changes only this report, its sanitized numeric metrics and the results index. Runtime sources, service configuration and deployment are unchanged. Private paths, process identifiers, credentials, configuration contents, raw logs, whole raw receipts, model payloads, generated text and output-ID arrays are excluded.
