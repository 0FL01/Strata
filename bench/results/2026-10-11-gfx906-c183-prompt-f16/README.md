# c183 prompt F16: approximate exploratory PP screen

The original c183 binary's existing **HIP_PROMPT_F16 flag, explicitly 0→1**, was tested in one fixed-order OFF→ON pair: 65,536 prompt tokens and one output per arm. No new build or patch was used.

- Prompt time: **101,333.6→81,985.9 ms**, saving **19,347.7 ms**
- PP: **646.735→799.357 tokens/s**, a descriptive **+23.598814% throughput** change and **19.093075% prompt-wall reduction**
- All 16 progress intervals improved by **1,087–1,866 ms**; 19,348 ms summed interval savings plus **−0.3 ms** tail savings reconcile the total

Both first outputs match the historical first token; INFO matches and activation on both owners was verified. Decode cache hits differ **469→468**, with 480 lookups each. Those counters begin after PP and do not explain the 19.35-second PP saving. Detailed PP route-work counters are unavailable, so PP work equality is unestablished.

**This changes operand/output rounding and remains approximate.** Hidden tensors, logits and GEMM outputs were not scanned for finiteness. One matching token establishes neither quality, full-trajectory parity nor TG equivalence. The ordered pair is not balanced performance qualification; external multi-feature table gains are not isolated F16 evidence.

Independent actual audit: **223 checks PASS**. Cleanup passed, API stayed stopped, final sampled maximum **55 C**. No production promotion or PR. [Aggregate metrics and provenance hashes](metrics.json).
