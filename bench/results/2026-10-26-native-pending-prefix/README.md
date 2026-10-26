# Native pending-prefix prototype

Experimental, default OFF: STRATA_PIPELINE_PENDING_PREFIX=1. Only admitted non-batch text pipeline-2 requests with maximum verification width two, no merge, suffix, lookup, coupled sampler or history penalty are eligible. The host planner bounds both fresh and pre-staged verification widths before launch, leaving one generated token pending at a finite natural output limit. No recurrent state is truncated.

## Evidence

The control rebuild exactly reproduced the selected native executable. Only the host generation object changed among 139 linked objects; all compiled device images remained bit-identical. Actual-source CPU fixtures passed 236 cases in each regular and UBSan build.

One fixed protocol process ran greedy and temperature-1 sampling (top-p .95, top-k 20, seed 23456). All 18 calls and 44 output token IDs matched the retained short reference. Caps one through four were immediately followed by an empty-append continuation: all eight reused the prompt minus one token and read exactly one token. Caps three and four exercised accepted width-two verification; cap two correctly offered no draft under the new bound.

Direct-live attribution is source-derived, not a runtime route label: matching live state is selected first and equal-length parked/checkpoint state cannot override it. Complete request logs had no contradictory restore. Independent audit replayed request summaries, completion records and activation markers.

## Limits and status

This is a short native correctness/cache mechanism gate, not task or performance qualification. EOS, STOP, full-state equality, long-context behavior and general sampled-distribution equivalence remain unproven. Both sampling profiles happened to produce the same short reference. The prototype remains default OFF; baseline, public main and frontend eligibility are unchanged.

The preceding frontend-only sampled experiment remains mixed: a no-wrap answer split introduced a 3077-token reread. This prototype is intended to test that specific downside, not erase its result or claim a speedup.

## Targeted sampled no-wrap task pilot

A single previously negative seed-12345 dependency-repair task used the existing experimental frontend cap plus this native bound. All six normalized turns exactly matched the original baseline: reasoning, final content, tool names/arguments, prompt/output counts and repaired file. All 14 hidden and three visible checks passed. The shared baseline explanation defect remains; this is not a general prose-quality claim.

The artificial answer continuation reused 12,838 of 12,839 prompt tokens and read one token (rounded native PP: 1 ms), replacing the frontend-only negative's 3,077-token reread (9,086 ms). The original negative is retained. This task delivered 4,722 tokens with nine tool calls. Native work changed: accepted/offered drafts were 1,880/2,376 versus the original 1,882/2,378, so delivered trajectory parity must not be described as native-work parity.

Task wall 101.796 s is descriptive only: the controls were retained, not freshly matched. This targeted mechanism result does not qualify general performance or promote the candidate. At that stage, the other five frozen sampled task/seed cases remained to be checked.

## Fixed six-case sampled quality coverage

Completed the remaining five predeclared cases without changing code, seeds, sampling or budgets. All six final task oracles passed: 22,793 delivered output tokens, 51 tool calls and 40 turns. All three resolver seeds and dependency-task seeds 12345/23456 exactly matched their original normalized trajectories and patches. Dependency seed34567 exactly matched the previously retained frontend-only variant, not the original baseline; that distinction remains a limitation rather than being normalized away.

Both wrapped dependency cases retained a 19-token continuation. The no-wrap case retained the one-token empty-append continuation. Later canonical-prompt rereads remained unchanged and are not claimed fixed. The resolver23456 intermediate visible-test failure followed by a successful repair is retained, as are shared explanation defects.

Those quality/mechanism checks used retained controls and did not establish fresh performance qualification. The subsequent fresh screen is reported below; universal state/distribution equivalence, public defaults and production remain outside its scope.

## Admission and termination limits

Width planning changes only under the exact experimental flag and admitted pipeline profile. Valid unsupported routes retain their existing width planning. Checked context validation runs before route eligibility when the flag is enabled; invalid unsupported GEN/GENI requests can therefore receive a different validation error. This is not general parser hardening: the flag-OFF path and earlier parsing/image paths retain their previous behavior and risks.

Natural finite length completion is the proof domain, not a runtime filter: an admitted request can still encounter EOS, cancellation or nonfinite output. Existing handling is untouched, but the pending-prefix guarantee does not cover those terminations. No blind truncation or recurrent-state mutation was added.

## Prospective fresh end-task screen

All 12 predeclared fresh runs completed, with three AB and three BA pairs. All final external task oracles passed. The equally weighted six-case geometric mean B/A task-wall ratio was **0.9716906312**, a **2.83094% reduction**. This passes the frozen engineering screen (at least 1% aggregate reduction, both wrapped cases improve, quality retained and no structural empty-append reread). It is one pair per case, not a confidence estimate or universal speed claim.

| Task / seed | A wall (s) | B wall (s) | B wall change | Cold PP A/B (s) |
|---|---:|---:|---:|---:|
| resolver / 12345 | 53.133 | 52.636 | -0.935% | 17.673 / 16.864 |
| jobgraph / 12345 | 105.157 | 101.437 | -3.538% | 19.961 / 16.585 |
| resolver / 23456 | 62.563 | 63.883 | +2.110% | 16.881 / 18.388 |
| jobgraph / 23456 | 158.582 | 149.902 | -5.473% | 16.827 / 16.638 |
| resolver / 34567 | 78.200 | 77.802 | -0.508% | 16.727 / 18.382 |
| jobgraph / 34567 | 125.174 | 114.814 | -8.277% | 19.338 / 16.743 |

Five pairs retained exact normalized reasoning/content/tool arguments and repair. Dependency seed34567 retained its previously documented per-variant repair/output difference (4,409 versus 4,358 outputs); its comparison is complete-task quality and wall, not identical-work speed. The aggregate must be interpreted accordingly.

Both wrapped continuations read 19 instead of 3,095 tokens. Their rounded native PP fell 9.043 to 0.131 s and 9.036 to 0.170 s. The no-wrap split still read one token; resolver requests gained no extra GEN. Later canonical-prompt rereads remained.

The resolver23456 regression is retained. Cold PP varied materially, including 19.961 versus 16.585 s in the no-wrap dependency pair; first-turn TG also varied. Nothing was excluded, rerun, subtracted or normalized for admission. Therefore the full aggregate improvement is not attributed solely to the feature. Native work counts differ despite delivered parity in five pairs.

Baseline explanation defects and the resolver intermediate failed visible test followed by repair remain recorded. Experimental flags remain default OFF; this result does not itself change public main, production settings or the selected baseline.
