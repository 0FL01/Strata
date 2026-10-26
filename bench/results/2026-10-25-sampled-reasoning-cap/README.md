# Sampled reasoning-cap experiment — mixed, not promoted

Date: 2026-10-25. This is an isolated experimental branch, not a main/default change.

## Fixed scope

Reasoning ON; temperature 1, top_p 0.95, top_k 20, min_p 0; neutral penalties.
Seeds 12345, 23456 and 34567 were declared before baseline outcomes.
Two synthetic repair tasks use real bounded tools and external value oracles.
Output budget is 4096 per turn, effective reasoning budget 3072, with unchanged
12-turn / 24-tool / 16384-total-output limits. This controlled policy is not
evidence of actual client request allowances or overrides.

Native executable SHA256:
`04761771491379c012b29bbc969628339cc0c98bf0cd7471277acf5bf6872176`,
HC BF16 clone plus wide dequantization, pipeline2/maxT2, uncoupled drafting.
No native code changed. Both frontend flags are required:
`STRATA_REASONING_NATIVE_CAP=1` and `STRATA_REASONING_NATIVE_CAP_SAMPLED=1`.
The second flag defaults OFF and admits only the exact profile and three seeds
above, with the existing text/nonbatch/neutral-penalty/argv guards.
Greedy behavior is unchanged. This is not production-general sampled admission.

Source/test commit: `8b8ee3cb63d6b4dd79666c77463d50481405634d`.
All 379 CPU tests passed: existing 360 plus 19 sampled admission/Service tests.
A fixed nine-call native smoke passed 22 IDs and fresh DONE checks. Caps 1/2
used direct live state; caps 3/4 used parked state. Accepted-T2 overflow was
exercised; EOS-at-cap was not. The short sampled reference happened to equal
greedy, so this is not diverse-sampling or distributional equivalence proof.

## Baseline and development evidence

All six fixed baseline tasks passed their final external oracles. Two of three
dependency-task seeds wrapped at the reasoning budget; no resolver seed did.
The seed-23456 development candidate preserved all nine normalized turns and
repair/tool work, reducing the wrap reread from 3095 to 19 tokens. Its whole
task timing also changed with cold PP, so it was excluded from qualification.

Normalization removes only nondeterministic tool-call IDs; it retains full
reasoning, content, tool names, arguments and output counts. It is not raw
native-token-ID equivalence.

## Prospective eight-run validation

The first four candidate cases reference retained baseline quality/trajectories,
not fresh timing controls. The final four are fresh mirrored seed pairs:
A23456, B23456, B34567, A34567. A uses the same source with both flags unset.
No retries, seed selection, budget changes or outcome-dependent tuning occurred.

| Task | Seed | Variant | Task wall s | Service output | Tools | Native PP s | Native TG s |
|---|---:|:---:|---:|---:|---:|---:|---:|
| Resolver | 12345 | B | 52.172284 | 1624 | 8 | 25.708 | 25.284 |
| Resolver | 23456 | B | 62.739482 | 2161 | 8 | 26.720 | 34.512 |
| Resolver | 34567 | B | 76.682960 | 2929 | 9 | 26.514 | 48.989 |
| Dependency | 12345 | B | 113.931552 | 4759 | 10 | 38.257 | 74.556 |
| Dependency | 23456 | A | 159.018021 | 6999 | 10 | 47.478 | 110.400 |
| Dependency | 23456 | B | 152.199864 | 6999 | 10 | 40.378 | 110.639 |
| Dependency | 34567 | B | 113.100441 | 4358 | 7 | 34.861 | 77.076 |
| Dependency | 34567 | A | 122.789868 | 4409 | 7 | 43.541 | 78.198 |

PP/TG are rounded native host-inclusive phase receipts, not pure device times.
Startup is separate from task wall. No pooled cohort gain or statistical
confidence claim is made.

## Findings

- All eight final runs pass external oracles and cleanup; all six candidate
  task/seed cases produce correct allowed repairs. Intermediate schema
  rejections and a resolver visible-test failure before repair are retained.
- All three resolver trajectories match their retained controls exactly.
- Fresh seed23456 preserves the complete nine-turn trajectory and patch.
  Wrapped Service turn: 64.354450 to 55.545867 seconds (13.6876% shorter).
  Wrap reread: 3095 to 19 tokens; PP 9.043 to 0.132 seconds.
  Candidate cold PP is worse: 18.793 versus 16.797 seconds.
- Fresh seed34567 preserves pre-wrap reasoning and reduces wrap reread
  3095 to 19 tokens (PP 9.149 to 0.171 seconds), but patch arguments and later
  output differ. The candidate factors edge indexing into local variables and
  renames another local; this is not merely alpha-renaming. Both repairs pass,
  but the wrapped-turn 79.605 to 70.413 seconds is not equal-work qualification.
- **The no-wrap seed12345 is a structural regression.** Reasoning ends at 2996
  tokens, but total patch output crosses the artificial native cap of 3072.
  Transparent answer continuation rereads 3077 tokens, costing 9.086 seconds PP.
  The first four delivered turns, including the patch, remain exact; later tool
  work differs. Task wall is 113.932 seconds versus retained 101.616 seconds,
  with 4759/10 versus 4722/9 outputs/tools. The retained comparison is not a
  fresh performance pair, but the additional reread is directly observed.
- Later canonical-prompt fallback after wrapped turns remains: the cap does
  not solve parsed-text re-tokenization differences. For seed23456 the next
  read remains 3473 tokens. Exact cache validation must not be bypassed.
- A wrap inserts 18 tokens. Baseline STOP drains two extra native tokens;
  capped native completion removes that drain. Service/native counts are
  reconciled separately, not mislabeled as a 16-token wrap.
- Known minor explanation errors remain baseline-relative: duplicate-emission
  wording in seed12345 and premature-termination wording in seed23456.
  No new material false execution/completion claim was found. Correct repair
  is not a claim of perfect prose or general agent competence.

## Verdict and preservation

**Task quality PASS; optimization MIXED; no broad sampled-cap promotion.**
The no-wrap cost counts against the candidate despite gains in wrapped cases.
The selected sampled comparator keeps both cooperative flags unset.
Published greedy branch and main remain unchanged.

Runtime evidence manifest SHA256:
`5cfa55a022ee95a0a84e98de029ca9cfeb41c94a80f960253a1ebadb9a92c673`.
Result SHA256:
`5c53fd67fccf53ad68021298651d49f7fea7307951c1f305cdd37589426bbd39`.

A possible output-budget-aware verification width is source-only future work.
Speculative front state may already be running; a late width clamp or blind
recurrent-state truncation is not safe. No such native change was built or run.
No raw logs, private paths, host inventory, weights or credentials are included.
