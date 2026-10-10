# Primary-only HC W-negative cache: parked after model ABBA

Decision: **PARK**. The predeclared 1% mean PP gate was not met. Mean PP changed **+0.2101832693%** and TG **−0.0168454149%**. The conservative TG zero-percent floor also failed (mean and first pair); this is not evidence of a statistically significant TG regression. No rerun, peer expansion, promotion or deployment follows.

## Actual measurement

Two gfx906 GPUs; 65,536 cold input tokens and 1,024 outputs in each fresh process. Fixed A1/B1/B2/A2 sequence on 2026-10-10, summary interval 06:57:08.178883–07:07:14.863359 UTC. A is the retained combined R&D c183 control, not the stable ce deployment or stock upstream. B adds only the primary-stage cache experiment to that frozen stack. The stable ce deployment is unchanged; the benchmark cleanup left the API stopped.

| Arm | PP time, ms | Decode time, ms | PP, tokens/s | TG, tokens/s |
| --- | ---: | ---: | ---: | ---: |
| A1 | 101298.7 | 19003.2 | 646.9579570123 | 53.8856613623 |
| B1 | 101099.2 | 19019.3 | 648.2346052194 | 53.8400466894 |
| B2 | 101145.6 | 19011.1 | 647.9372310807 | 53.8632693532 |
| A2 | 101371.2 | 19020.8 | 646.4952570355 | 53.8358008075 |

Arithmetic means of per-arm throughput: PP **646.7266070239052 → 648.0859181500836 tokens/s**; TG **53.86073108491694 → 53.85165802129143 tokens/s**. Throughput uses 65,536 / prompt seconds and 1,024 / decode seconds; gains compare candidate and baseline arithmetic means. Matched B1/A1 and B2/A2 PP gains are **+0.19733093832592363% / +0.2230447987850992%**; TG gains are **−0.08465085465815259% / +0.05102282350837317%**. Both PP pairs are positive, but the 1% gate is unchanged.

All four native exits and the wrapper exit were zero, complete raw lifetimes were recovered, and cleanup passed. All 1,024 output IDs in each arm match one another and the historical reference. The public derivative retains their receipt hashes and counts, not the token arrays or raw model output. The independent raw audit passed.

Available counters match in all arms: accepted/offered **648/872**, cache hits/lookups **582,049/600,000**, prompt reused/read **0/65,536**, suffix windows/accepted/offered **5/9/16**, and zero RAM blobs, file blobs, offloaded experts and file-read MB. The five optional fields decode_windows, lookup_chain_accepted/offered and native_suffix_accepted/offered were unavailable and remain null. Native done-field count is 16. The timing-trained adaptive execution policy and aggregate counter equality do not prove complete constant work. Four runs do not establish statistical significance, broad repeatability or isolated removable guard cost.

## Qualification and implementation boundary

The same candidate binary was first qualified on 12,288 input tokens and one output, with runtime qualification output enabled; timing disabled that output without rebuilding. Exact reference output parity passed. Actual primary counters were **324 candidates, 11 learned W-negative keys and 22 hits**; **302 physical guards is inferred as 324−22**, not an independent measured counter. Route attempts/taken were **324/99 primary and 252/104 peer**. All 11 negative keys had mask 4 and two hits. This is a frozen-prefix qualification under the reviewed caller contract, not general correctness.

The cache is a bounded 256-entry host array scoped to one eligible primary public run, reached through thread-local state, cleared on request completion and exception unwind. Admission is restricted to the reviewed nonconcurrent generate flow with immutable weights and fixed run context. Arbitrary weight-mutating/reset callbacks and racing lifetime operations are excluded. Peer stages retain baseline guards. No public Gemm layout change and no GPU kernel changes were made. The source/CPU, actual build, 55-device-module byte equality and linked TLS audits passed. This does not broaden the caller contract or guarantee peer drain completion if the existing drain throws.

Runtime opt-in is exact STRATA_HC_WNEG_PRIMARY=1. The original eligibility, scratch/overlap, policy and diagnostic exclusions remain. A certified W-negative hit selects the existing native BF16 fallback. X-negative observations do not populate this cache. No extrapolation from 12K hit counts to measured 64K savings is claimed.

## Provenance and public derivative

- Baseline binary SHA-256: c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049
- Candidate binary SHA-256: f19065bc82cb55d30375c51ffed8bd828e4165b5c5ffb69bcc313677103b6fb2
- Raw ABBA archive SHA-256: 971fdeb3f114152e65549d86e35e7a175f8642ff991299e9a5cf328c09fcbf87 (51,809 bytes)
- Independent ABBA audit SHA-256: c2d7f23f5c80eed11f50ec923fad7afb0b8c55e9bb234d25f58f43caca540cbc

[Numeric metrics](metrics.json) preserve raw phase and wall times, per-arm throughput, all pair/mean calculations, policy thresholds, flags, numeric runtime configuration, GPU samples, optional-counter availability, and source/build/qualification/raw-audit hashes. Model/prompt payloads, output IDs, raw logs, private filesystem paths, pointers and credentials are excluded. Raw audit seals describe separately retained evidence; this archive does not contain an independently buildable snapshot of the complete measured private stack.

This update changes only this report, its metrics and the archive index. It introduces no runtime source, implementation patch, PR change or service change.
