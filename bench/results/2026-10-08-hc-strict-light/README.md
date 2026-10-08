# Strict-input HC conversion screen

Hypothesis: HC read is about one fifth of instrumented 4K prefill on the current exact stack. The existing strict-input FP16 diagnostic spends unnecessary work collecting audit counts, maxima, and output scans. Replace diagnostic mismatch counts with fused boolean flags while retaining range checks, original-value bit comparison, the existing host decision, and native fallback. The plausible whole-prefill opportunity is a few percent; one short matched screen can falsify it.

Prototype only, not a production promotion or universal output-equivalence claim. Exact input conversion does not by itself prove that another GEMM implementation preserves every accumulation result.

- Patch: 15 added / 5 removed lines across conversion and component probe.
- GPU0: AUDIT0/1 gave identical eligibility and output hashes for all four HC shapes with random representable inputs, tiny W, tiny X, and signed zero. All 32 full-output native comparisons passed. Random inputs took the route; tiny/signed-zero cases fell back.
- Fresh 4K +256-output screen: current best PP347.676 tok/s; same prototype with route off348.101; strict route358.434. Greedy output IDs match; TG stayed about54.9 tok/s. This is one observation per arm, not qualification.
- Runtime coverage: 33/108 calls on the primary and39/84 on the secondary took the strict route; the rest used native BF16.
- Next: reverse 4K repeat, longer generation and64K code/Russian, then only the further checks justified by the result.

Current best baseline binary: ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14.
Prototype binary: 314e827d1f8d1702b06090f75e53e887f72f2db986dd7113fa8eb03bfa1e5972.
Standalone prototype patch: bd6e0d26ef3a8ec865e08d1311d043d9434da4bb2ab2896d5bc5d87e07838b44.

Systemic candidates deprioritized by the refreshed profile: gather/group/copy wait are below1% of4K prompt time together; prior-negative split overlap has no new supporting idle-gap evidence. Stager sleeping exists in newer upstream and needs active staging-job evidence before a local test.

## Follow-up model qualification

Six fresh runs with 1024 generated tokens: reverse-order 4K, code 64K, Russian 64K. Each pair produced identical complete token-ID sequences. Best-known/strict PP in tok/s:

- 4K: 347.817226 / 358.117088, +2.9613%
- Code 64K: 598.253148 / 608.261125, +1.6729%
- Russian 64K: 597.469942 / 608.092936, +1.7780%

TG stayed effectively unchanged. These are single pairs per 64K workload; the earlier 4K screen independently agrees. In total, 72 full-output component comparisons passed across the two cards, including overflow boundaries, tiny operands and signed zero. No actual 200K model request, tools/vision/cache qualification, or production promotion is claimed for this candidate. The existing working build was restored after the tests.
