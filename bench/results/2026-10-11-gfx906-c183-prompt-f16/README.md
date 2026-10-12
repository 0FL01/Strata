# c183 prompt F16: approximate exploratory PP screen

The original c183 binary's existing **HIP_PROMPT_F16 flag, explicitly 0→1**, was tested in one fixed-order OFF→ON pair: 65,536 prompt tokens and one output per arm. No new build or patch was used.

- Prompt time: **101,333.6→81,985.9 ms**, saving **19,347.7 ms**
- PP: **646.735→799.357 tokens/s**, a descriptive **+23.598814% throughput** change and **19.093075% prompt-wall reduction**
- All 16 progress intervals improved by **1,087–1,866 ms**; 19,348 ms summed interval savings plus **−0.3 ms** tail savings reconcile the total

Both first outputs match the historical first token; INFO matches and activation on both owners was verified. Decode cache hits differ **469→468**, with 480 lookups each. Those counters begin after PP and do not explain the 19.35-second PP saving. Detailed PP route-work counters are unavailable, so PP work equality is unestablished.

**This changes operand/output rounding and remains approximate.** Hidden tensors, logits and GEMM outputs were not scanned for finiteness. One matching token establishes neither quality, full-trajectory parity nor TG equivalence. The ordered pair is not balanced performance qualification; external multi-feature table gains are not isolated F16 evidence.

Independent actual audit: **223 checks PASS**. Cleanup passed, API stayed stopped, final sampled maximum **55 C**. No production promotion or PR. [Aggregate metrics and provenance hashes](metrics.json).

## Follow-on: 1,024-output trajectory diverges

A separate fixed-order 64K/1,024-output OFF→ON pair preserves all **1,024 historical outputs with OFF**. ON first differs at **zero-based index 13 (the 14th token)** and differs at **986 positions** overall. The earlier one-output observation remains valid but does not imply trajectory parity.

PP measured **646.841→799.522 tokens/s (+23.604045%)**, with all 16 prompt-progress intervals faster. Observed TG was **53.92255→55.58722 tokens/s (+3.087154%) on different trajectories and decode work**, not an isolated or equal-work speedup:

- Accepted/offered: **647/868→678/875**
- Decode cache hits/lookups: **580,670/598,560→557,414/587,520**
- Cache misses: **17,890→30,106**

INFO matches. The **223-check actual audit passed**; cleanup passed, API stayed stopped, final sampled maximum **53 C**. Approximate arithmetic, unseen hidden/logit/output finiteness and the single ordered pair remain limiting. Neither quality preservation nor quality loss is established. **Quality smoke is pending. No further speed runs before quality review; no PR or promotion.**

## Follow-on: narrow USER-text likelihood diagnosis (2026-10-12)

Two new public-repository fixtures (4K docs / 64K code) score **512 teacher-forced USER-text targets each**. Their role sequence is user excerpt → assistant acknowledgment → user disjoint excerpt. **This is not an assistant-task benchmark.** Scored fields are finite and every target position is aligned.

Primary unconditional mean-NLL changes, ON minus OFF:

- 4K docs: **+0.531360**, perplexity ratio **1.701245**; NLL worsens at **492/512** positions
- 64K code: **+0.255897**, perplexity ratio **1.291619**; NLL worsens at **386/512** positions

OFF/ON argmax agreement remains **98.4375% / 95.703125%**; agreement does not establish probability calibration. Post-run arithmetic localizes most aggregate NLL increase to the **im_end probability-mass penalty: +0.519265 / +0.227216**. Conditional NLL changes after excluding im_end are **+0.012095 / +0.028681**. **The unconditional results remain primary; this conditional diagnostic does not replace them.** Every scored position is retained.

These findings establish worse target likelihood on these USER-text fixtures, **not general assistant-quality degradation or a quality pass**. They do not identify the numerical cause, establish full-vocabulary KL or prove all hidden tensors finite. The actual audit passed **423 checks**, with an independent score-arithmetic review; cleanup passed, API stayed stopped, final sampled maximum **53 C**.

The earlier pending quality check has yielded this narrow diagnosis. Assistant-role 4K fixture preparation is next, with no GPU execution for it yet. No global F16 promotion.
