# c183 Q5 head R2: below the practical filter

**DEPRIORITIZE_BELOW_ONE_PERCENT_FIXED_SCENARIO.** One GPU1 process compared the literal c183 archive, a new-translation-unit R1 control and one R2 candidate. The original archive's compilation-source identity remains unproven.

Real main-head metadata is Q5_K/type13, K=2560, N=248320; the test uses **437,043,200 bytes (416.80 MiB) of synthetic valid-format weights**. All five full-output byte-parity cases passed, including an odd-row tail and full-size T=1–4, with direct/captured checks, canaries and immutable activations.

Timing retained **72 samples**, all six arm permutations per T, 16 warmups and four graph calls per sample. Archive-minus-R2 paired median savings for T=1/2/3/4 are **+0.024040 / +0.101100 / −0.014980 / +0.476160 ms**. **All six T3 pairs regress.** R1 control timings closely match the archive.

The predeclared 379-call/1,247-row scenario spans 6,165 possible histograms: **48.3479–139.8509 ms**, or **0.2545–0.7362%** of the 18,995.85 ms reference. Even its maximum misses the **1% practical filter**. This synthetic captured-component exposure is not a model wall-time prediction; normal suffix-enabled T6 is outside the scenario.

**Park R2.** No T-specific variants, engine patch or model run. Adjacent generic multicolumn reuse is bypassed on wave64 and was not added; earlier R4 preparation has no execution evidence.

Independent actual audit: **125 checks PASS**. Cleanup passed, API stayed stopped, final sampled maximum **48 C**. [Aggregate metrics and provenance hashes](metrics.json).
