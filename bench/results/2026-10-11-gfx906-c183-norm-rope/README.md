# c183 NORM_ROPE: bounded repair, insufficient exposure

**Park engine integration and model timing.** The original fused route fails finite byte parity; one isolated candidate passes the bounded component suite but offers too little conditional exposure to justify a model port.

- **Original:** first owner0 Q case (T=1, 24 rows, head dimension 256, stride 512) differs in 172 FP32 elements. The first difference is one ULP. Execution stopped before ON, captured replay, timing or owner1. Actual audit: 119 checks PASS; correctness FAIL.
- **Candidate:** HIP register barriers materialize normalized a/b, with literal separate rotation expressions; RMS, angle and reduction stay unchanged. This is a separately compiled component object, with no engine patch. Owner0 first passed 48 finite cases (229-check audit). The later both-owner suite passed 96 finite cases; eight additional NaN/Inf observations matched but remain outside the finite contract. Changing both expressions and materialization does not isolate the original cause.
- **Captured cost:** all 384 paired comparisons across 768 timing records are positive; Q saves about 4.6–4.7 us, K/index about 2.2 us. The final actual audit passed 401 checks.

For the canonical OFF baseline, the fixed suffix-OFF scenario gives **20.683–20.801 ms on GPU0** and **20.618–20.679 ms on GPU1**, each about **0.109%** of the 18,995.85 ms reference. It uses 379 inferred windows, 1,247 rows, six QSA layers per owner and 6,165 possible histograms. Separate GPU1 MTP scenarios are Q at most **5.280 ms** and eligible K **0–2.471 ms**. Do not sum overlapping owners or MTP stages.

OFF/ON here separately characterize standalone RoPE CTA128/CTA32 launch geometry, not RMS reduction. Synthetic component savings are not model speedups, universal equivalence or critical-path bounds; normal suffix-enabled T6 is outside this scenario. Cleanup passed, API stayed stopped, final sampled maximum **48 C**.

[Aggregate metrics and provenance hashes](metrics.json). No production change, model qualification or PR.
