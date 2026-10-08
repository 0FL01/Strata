# Integrated exact gfx906 live release — 2026-10-08

## Scope and provenance

R&D is paused by request. This release combines already-qualified exact paths; it does not start new optimization experiments or an upstream PR.

- Source assembly: b6731bf; documentation head before this report: 3bf181f71bebd9749ded988ee6b7413358b84826.
- Qualified release binary SHA-256: ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14.
- Deployment patch SHA-256: b1bb1c99e225ab425e368ac2a10cfd013cb41cbe3dfd94c757104c99980f70a3.
- Pinned runtime image: sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646.
- Model: Qwen3.8-Flash-Next-GSQ-RCO-abliterated-IQ3_XXS-Q2_0; two gfx906 16-GiB GPUs and Xeon E5-2698B v3.
- The existing integrated binary was checksum-verified, requalified, then promoted. It was not rebuilt from later experimental working trees.

Selected paths: Q2 gate/up unpack mode16, CPU Q2 AVX2 spread, guarded gfx906 top-k2, MMVF_ROWS1 with RPB4, fused SwiGLU, GDN_HEAD1/PP2/CONVL2=1/NOY=1, MTP draft window16384, stock HIGH GPU mode. Power caps remain190W per card. Target context204800, INT8 KV with32768 resident tokens, expert slots9900+9178=19078, later VRAM reserve623MiB. Requested reserve is not the same quantity as reported remaining free memory.

Excluded: approximate HC FP16 paths (including scaled candidates), unqualified strict exact-input HC experiment, MTP8K, QFUSE fast-tail path, PR1465 norm reuse, and previous negative pipeline/overlap experiments.

## Fresh controlled benchmark

Twelve fresh-process runs, ABBA for each workload, 1024 generated tokens per run. A is the **previous already-tuned production configuration**, binary3fdb12152c5e148c7af241cc4cde0e4f71494f657bba48f6ca9bb363b90757f6, mode15, CPU spread/top-k off, MTP32768, GPU AUTO. B is the integrated release above. Both arms retain earlier MMVF/SwiGLU/GDN tuning, fixed placement, identical context/quantization, expert residency, prompts, greedy sampling and seeds. Prompt reuse is disabled.

These are incremental gains over prior production, not a stock-upstream comparison and not a sum of isolated speedups.

| Workload | A decode tok/s | B decode tok/s | Decode gain | A prefill tok/s | B prefill tok/s |
|---|---:|---:|---:|---:|---:|
| code 4096 | 53.428 | 56.085 | +4.97% | 347.520 | 348.313 |
| code 65536 | 47.297 | 50.550 | +6.88% | 597.447 | 597.806 |
| ru 65536 | 49.744 | 52.685 | +5.91% | 597.472 | 597.486 |

Each cell is the arithmetic mean of two runs. All four output-token ID sequences agree within each workload. Both B decode observations exceed both A observations in all three workloads. The sample is small; no confidence interval or broad quality claim is made.

Prefill is effectively unchanged. For a cold prompt plus1024 generated tokens, measured native engine total time fell3.02% at4K,1.11% for code64K, and0.88% for Russian64K; decode speedup alone is not the end-to-end speedup. Loader time is separately retained in analysis.json.

Full204800 capacity was configured throughout. Actual200000-token occupancy was qualified in the previous exact-stack report; this fresh run does not repeat that capacity test.

## Live qualification

See live-qualification.json for the executed deployment and API checks. CPU vision, existing API authentication, model alias support, sampling defaults and conversation cache are retained. Live API is left running for user testing; no parallel GPU R&D jobs are intended.

The synthetic API coverage is a named tool call/result roundtrip, two CPU-only image requests, text after vision, A/title/A conversation-cache restore, unauthenticated models401 and disabled UI404. This is not a replay of the user's real agent task or a broad task-quality benchmark.

HIGH is the current GPU performance setting, not a newly installed boot-time policy. The API keeps its existing Docker unless-stopped restart policy.

## Evidence

- analysis.json: all twelve per-run metrics and output-ID hashes, group comparisons.
- live-qualification.json: deployment and synthetic API verification.
- Existing source/build and component evidence: ../2026-10-07-gfx906-exact-stack/.
- Raw receipts remain on the authorized campaign hosts; credentials and password-bearing configurations are excluded from publication.
