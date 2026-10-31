# Opt-in gfx906 draft-shortlist profile (R&D, not deployed)

## What to reuse
Use Strata's existing draft-only vocabulary override; no QEngine implementation is required.
QEngine research suggested checking static draft head reduction, but this fork already implements it.
The tested subset is the repository's `data/draft_vocab_cyrillic.bin`:
58963 distinct token IDs, SHA256
`25d7fd1670a2e0ec885868d1718d410a3baab03bceeacf0a156cf93ffe4e1ef4`.

Append the following **two arguments** to a copy of your existing native arguments
(replace an existing override rather than duplicating it):

```text
--mtp-draft-vocab /absolute/path/to/Strata/data/draft_vocab_cyrillic.bin
```

For the Python API server, these are entries in its existing `cfg["args"]` array;
`engine_args()` forwards that array to the native engine. This is a configuration
fragment, not a replacement for the complete model/server configuration.
The path must be visible inside the runtime container.
Restarting or deploying a production service is **not** part of this research profile.

## Evidence and scope
- Two cold 64K-input/4096-output pairs: TG +2.11% and +1.81%, every output ID exact.
- One short Russian prompt, repeated in reverse order: TG +38.9% and +46.6%;
  every 1024-token output exact, accepted drafts improve from 268/458 to 391/478.
  Whole request wall improves about 25-26%, but TTFT is worse in both pairs.
- One short English code task: every 1024-token output exact; single-pair TG +1.33%,
  too small and unreplicated to claim a general code-workload benefit.
- About 79.4 MiB less second-GPU READY memory at the same expert-cache capacity.
- No measured PP acceleration is attributed to the shortlist.
- All runs use deterministic greedy generation with fixed output lengths and EOS stopping disabled.
  The two short tasks do not establish performance on a broad language/task distribution.
  Synthetic 64K results do not establish varied long-context agent performance.

The target verifier and full target vocabulary remain unchanged. This does not remove
MTP weights or change target-model quantization. Reduced draft vocabulary can improve
or degrade draft acceptance by workload; do not assume smaller is always faster.

## Benchmark controls, not universal production settings
The measurements retained native SHA256
`731cbb6c886d4631e2ee71c5dc633de36b639288fc3a1acf30652a6518ac8180`,
the same model, split 27, context 262144, int8 KV/32768 resident, MTP spec6/maxdepth2,
PP cap4096, suffix0 and pipeline windows2.
Actual expert slots were held at9399 primary +8619 second to prevent the freed head
memory silently changing cache capacity. Tail skipping was explicitly disabled and
IQ multithreading threshold set to1 for exactness controls.
These are **not** claims about unchanged production-as-is behavior.

Do not copy the cache counts blindly onto another model/GPU/memory layout.
Keep your current settings and qualify the isolated shortlist change on representative
requests, token equality, TTFT and complete wall time before any deployment.

## Rollback
Remove the override to return to the MTP pack's original default `draft_vocab.bin`,
or restore the exact previous override if one existed. Preserve the original pack;
do not overwrite its vocabulary file. The research did not modify production files,
the native executable, model weights, or the existing API overlay.

See [complete experiment log](2026-10-31-qengine-gfx906-results.md).
