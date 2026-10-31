# QEngine transfer experiment log

Final status: this bounded round is complete. Earlier Next/pending paragraphs below are contemporaneous checkpoints, superseded by E006/E007 and the final decisions. No production deployment.
## E001: existing PP staging ring, 2026-10-31
Outcome: negative single-pair screen; retain 384 slots, do not promote 512.

Native baseline SHA-256: 731cbb6c886d4631e2ee71c5dc633de36b639288fc3a1acf30652a6518ac8180.
This is the previously deployed native build, not a newly rebuilt branch binary.
Both arms: 2 x gfx906, same model files (read-only mounts and unchanged filesystem identities),
layer split 27, context 262144, int8 KV with 32768 resident cells, PP cap 4096,
18018 expert slots (9399 primary), MTP spec 6 / maximum depth 2, min probability 0.5,
pipeline windows 2, suffix draft 0, temperature 0, top-k 1, seed 12345.
Exactness controls: STRATA_ROUTE_TAIL_SKIP=0, STRATA_IQ_MT_MIN=1.
Only STRATA_PREFILL_RING changed between 384 and 512. This profile is not production-as-is.

Cold 65536 input / 1024 output tokens:
- Ring 384: PP 610.5186 tok/s, TG 66.3500 tok/s, TTFT 107.7527 s, wall 122.8039 s.
- Ring 512: PP 588.6992 tok/s, TG 66.1918 tok/s, TTFT 111.7343 s, wall 126.8173 s.
- All 1024 output IDs match. Draft acceptance 457/517 in both.
- Expert transfers rise from 164512 to 168608. Larger staging borrows additional cache space.
- PP -3.57%, full wall +3.27% in this pair. No stability qualification, but no positive signal to pursue.
- Short 4096 / 128-token gate also matched exactly. Its PP differed about 1%; short TG had large variation despite identical accepted drafts, so it is not an attributed speed result.

The model corpus is a deterministic synthetic prompt reused from prior tests; this is not evidence for varied real agent traffic.
The GPU runner preserves full per-run command, output-token arrays, stderr and memory traces privately on remote storage.
Production remained stopped after owned test-container cleanup, as requested.

## E002: offline suffix opportunity analysis
QEngine's lookup-draft idea overlaps Strata's existing SuffixDrafter and disabled-in-production suffix option.
The generic tools/rnd_qengine_suffix_opportunity.cpp invokes the existing implementation with min match 3,
max match 64 and max proposal 6, scanning previously generated output without reading future output into the history.
It counts overlapping opportunities, not a scheduler replay or a speed estimate.
- Prior production-profile 4096-token trace: 1555 positions propose, 572 have >=2 correct next tokens, 389 have >=3.
- Prior controlled-profile trace: 2577 positions propose, 1071 have >=2 correct, 784 have >=3.
These are different output traces, not comparative performance results. Table capacity can differ from runtime.
Built with g++ -O2 -std=c++17; existing suffix_drafter unit tests pass. Empty input produces zero counts; oversized input rejects with exit 2.
Decision: one bounded GPU suffix-draft=3 screen against today's exact control is warranted.

## Next
E003 tests suffix drafting, then E004 screens PP cap 8192 after a short exactness gate.
8192 is not a free improvement: the existing HC BF16 clone is only qualified for chunk sizes 4096/4093,
so larger chunks use its generic fallback. No QEngine source code was copied.

## E003: existing suffix-draft=3, first screen
Both 128-token and 1024-token outputs matched their suffix-disabled control.
At cold 65536 / 1024, suffix=3 produced PP 587.0376, TG 64.9763,
TTFT 112.0549 s and wall 127.4307 s; accepted drafts 470/541 versus 457/517.
No TG gain in this pass. PP changed despite identical 164512 expert transfers and no PP feature change,
so the earlier ring single-pair PP delta must not be over-attributed. A repeated control is required.
A 4096-output pair remains pending because offline suffix opportunities differ later in the output.

## E004: PP cap 8192, rejected short screen
At 8192 input / 128 output, cap 4096 versus 8192:
- PP 430.5574 versus 370.8230 tok/s; TG 58.0446 versus 57.7357 tok/s.
- TTFT 19.4292 versus 22.4921 s; wall 21.2448 versus 24.3218 s.
- Actual chunks 4096 versus 8191; expert transfers 20564 versus 12616.
- Outputs diverged at zero-based index 89. The long-context candidate was not run.
Fewer transfers did not improve complete PP. Source inspection shows the current HC clone specializes
4096/4093, and larger chunks fall back; that is a possible explanation, not measured attribution.
No correctness or performance promotion.

## Source exclusions
- QEngine's shortlist is static corpus frequency ranking, not a dynamic per-context algorithm.
  Strata already provides static draft vocabulary selection. A 58963-token shipped Cyrillic subset
  is being screened against the current 106299-token subset with fixed expert-cache counts.
  It covers the same number of target tokens in the two historical traces, not proof of equal draft quality.
- QEngine's sparse attention union-inflation fallback has no reachable equivalent gap in gfx906.
  qsa_prompt_attn.cu returns false under STRATA_HIP_GFX906; prefill.cpp invokes qsa_decode_attn_batch.
  That kernel indexes each query's own selected IDs, not a cross-query union. STRATA_SEL_OVERLAP computes
  union ratios only for diagnostics. No redundant kernel port or GPU test is warranted.

## E005: fixed-cache draft shortlist and longer suffix screen
Current native 731... baseline is retained; only the existing draft-only vocabulary path changes.
The verifier remains full-vocabulary. Explicit cache settings freeze actual slots at 9399 + 8619;
the shortlist cannot silently spend saved memory on extra expert slots.

| Cold input / output | Arm | PP tok/s | TG tok/s | TTFT s | Request wall s |
|---|---|---:|---:|---:|---:|
| 65536 / 1024 | repeated control, 106299 rows | 609.8698 | 65.0105 | 107.8636 | 123.2362 |
| 65536 / 1024 | Cyrillic shortlist, 58963 rows | 611.3889 | 66.4452 | 107.5979 | 122.6273 |
| 65536 / 4096 | control, 106299 rows | 608.1680 | 72.3940 | 108.1642 | 164.3627 |
| 65536 / 4096 | Cyrillic shortlist, 58963 rows | 608.0935 | 73.9179 | 108.1772 | 163.2094 |
| 65536 / 4096 | suffix=3, default shortlist | 610.6853 | 72.1916 | 107.7353 | 164.0840 |

All tested 128-, 1024- and 4096-token shortlist outputs match their control exactly.
Repeated control also matches the original 1024-token control.
The 4K shortlist pair has +2.11% TG and -0.70% whole-request wall, with essentially unchanged PP.
This is a small first-pair signal, NOT a qualified speedup: the original 1K control was 66.3500 TG,
close to the shortlist's 66.4452, whereas the fresh repeated control was 65.0105.
A reverse-order 4K repetition and two held-out Russian/code pairs are pending.
These held-out cases have short prompts (163/116 tokens), fixed 1024-token generation and disabled
EOS stopping; they do not qualify natural completion or varied long-context traffic.

Fixed-cache second-GPU READY memory falls by about 79.4 MiB in the 4K pair.
The shipped shortlist SHA256 is
25d7fd1670a2e0ec885868d1718d410a3baab03bceeacf0a156cf93ffe4e1ef4.
This is measurable memory saving, not removal of all MTP weights or a PP speedup.

Suffix=3 also matches all 4096 output IDs but produces no TG gain.
Only five suffix windows actually execute (21 of 22 draft tokens accepted).
The offline overlapping opportunity count was deliberately not a scheduler prediction.
Retain suffix=0; no further suffix grid is warranted from these results.

## PP phase diagnostic plan
Existing native dispatch receipts confirm HC clone execution for the eligible 4096 chunks,
and zero clone dispatches at cap 8192 on both GPUs.
A two-arm 8K/128 diagnostic using existing STRATA_PREFILL_TIMING is prepared.
It records all phases; the "hc read" phase includes more than the clone, so it cannot isolate clone
causality alone. Instrumented timings are not production performance qualification.
No new HC shape is enabled: the current 4096/4093 whitelist is retained.
Production stays stopped in R&D mode; original native/model/config/overlay rollback is preserved.

## E006: reverse-order and held-out qualification
The reverse 64K/4K pair preserved all 4096 output IDs:
- Shortlist: PP611.1135, TG73.6161, TTFT107.6485s, wall162.9066s.
- Control: PP595.4192, TG72.3045, TTFT110.4770s, wall166.7403s.
Together with the first pair, synthetic TG gains are +2.11% and +1.81%.
The control's PP variation is not caused by a changed PP algorithm; do not attribute all wall improvement to the shortlist.

| Short held-out task | Arm | TG tok/s | TTFT s | Wall s | Draft accepted/tested |
|---|---|---:|---:|---:|---:|
| Russian, first pair | control | 42.1793 | 2.5213 | 26.4199 | 268/458 |
| Russian, first pair | shortlist | 58.5843 | 2.6531 | 19.7575 | 391/478 |
| Russian, reverse pair | shortlist | 58.8969 | 3.3665 | 20.3698 | 391/478 |
| Russian, reverse pair | control | 40.1624 | 2.4678 | 27.5881 | 268/458 |
| English code, single pair | shortlist | 71.9789 | 2.2419 | 16.0827 | 448/512 |
| English code, single pair | control | 71.0371 | 2.3549 | 16.3945 | 448/512 |

All held-out 1024-token output IDs match; each Russian repeat also matches the original control.
Russian TG improves +38.9%/+46.6%, and request wall improves about25.2%/26.2%.
Unlike the small synthetic head-size benefit, this task also has substantially better draft acceptance.
TTFT is worse in both Russian pairs. Do not hide that tradeoff or promise universally faster responses.
Code's single-pair +1.33% TG is not separately qualified as a stable gain.
These short requests use163/116 input tokens and fixed1024 output tokens with EOS stopping disabled.
The language-specific result is not a representative Russian benchmark suite.

Decision: save a [tested opt-in shortlist profile](2026-10-31-qengine-gfx906-shortlist-profile.md).
No production default, model, native or API overlay is changed.

## E007: instrumented PP phase attribution
This is a diagnostic pair, not performance qualification.
For8192 input/128 output, PP cap4096 versus8192:
- Native PP wall18.7681s versus22.3881s.
- Primary measured GPU timeline (including waits)13.059s versus12.211s.
- Summed peer measured GPU timelines (including waits)9.993s versus9.071s.
- Combined "hc read" phase4.791s versus4.986s, only+0.195s versus+3.620s total wall.
- HC clone receipts: eligible4096 chunks execute;8191 executes zero clone dispatches.
- Cap4096 makes bulk chunks4096+4095; cap8192 makes one8191 bulk chunk.
  The final input token is handled separately in both.
- Output divergence remains; no long-context8192 qualification was attempted.

Source prefill.cpp4743-4794 hands completed chunks asynchronously to the successor GPU,
alternating two buffers;4841 deliberately does not drain the successor at stage return.
This inter-GPU chunk handoff exists even when INFO reports prefill_pipe=0.
In the4096 diagnostic, the first peer chunk finishes before the primary stage summary.
With8192, primary wall12.237s plus peer wall9.719s nearly accounts for complete PP22.388s.
The lower sum of measured GPU timelines (including waits) but higher wall supports loss of chunk overlap as the main explanation.
Timing observers add events/synchronization; this is supporting attribution, not a proof that all
wall difference is overlap or a production-speed estimate.

Decision: park8192 HC whitelist expansion this round. Its shape gate is a qualification whitelist,
not a hard fixed-T kernel dimension, but the measured HC-phase increase is too small to explain
the regression, other chunk arithmetic already changes token output, and larger chunks lose overlap.
Do not broaden a default merely because a kernel can accept more rows.

## Deliverables and retained state
- [Machine-readable uninstrumented measurements](../../bench/results/2026-10-31-qengine-gfx906/measurements.json) contain22 runs.
- [Held-out prompt fixtures](../../bench/results/2026-10-31-qengine-gfx906/heldout-prompts.json) contain only researcher-authored synthetic text.
- [Instrumented phase runs/receipts](../../bench/results/2026-10-31-qengine-gfx906/phase-diagnostic.json) are stored separately to prevent pooling them with performance data.
- Existing suffix-drafter CPU tests and analyzer boundary checks passed; no native/kernel source was modified.
- Final preservation check: original container config/mounts unchanged, native SHA unchanged,
  recorded model-file identities unchanged, no running benchmark containers.
- Production remains intentionally OFF as requested; GPUs are idle. Original rollback artifacts remain private on remote storage.

## Remaining cache/transport eligibility
No additional transport kernel is justified by this round's trace.
The existing ring already budgets against the expert cache and borrows/refills its region
(prefill.cpp285-337,1327,1416,1605+,2302,2559). This is not a missing generic QEngine feature.
The cap4096 diagnostic exposes only30ms total compute-stream "wait copy" against18.768s PP.
That does not exclude hidden PCIe or host costs, but provides no positive case for enlarging staging;
the larger512 ring also failed its earlier screen.
A smaller ring is an available tuning knob, not a port: it might retain experts but could increase
DMA and change resident-versus-streamed numerics. Park it until missed-byte/admission tracing
establishes a concrete expected saving; do not start an arbitrary ring grid.
Existing piecewise handoff and persistent successor worker already provide inter-GPU overlap.
QEngine tensor-parallel/all-reduce work is not a direct fit for this layer-split runtime.
A separate topology/transfer bottleneck profile would be required to revive that direction.
