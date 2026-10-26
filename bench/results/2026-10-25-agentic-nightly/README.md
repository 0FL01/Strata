# Agentic R&D checkpoint — 2026-10-25

## Current research objective and selection
Optimize completed agent-task wall time subject to successful bounded tools and an external repair oracle. PP, TG and TTFT remain diagnostics rather than independent zero-regression vetoes. Reasoning is ON again after an explicit no-thinking viability experiment. Production API remains off.

Published main remains `f9b38e9e5d70cef7776f2a5bd6fed5e56872ec02`, the user-selected HC BF16 clone. Local research additionally selects wide dequantization. The experimental cooperative reasoning cap is restricted to its qualified 8K workload/profile; its public default remains OFF.

## Wide dequantization
Frozen original resolver: 8K ABBA and 64K BAAB, all eight hidden-oracle passes and normalized within-context trajectories/tool work identical. Equal-context geometric-mean task-wall reduction: **4.3850%** (8K 4.3169%, 64K 4.4531%).
Independent dependency-order task, 8K fresh ABBA: **1.9736%** task-wall reduction, both pairs positive and all trajectories/repairs exact. Nested TG duration rose about0.37%; preserved, not hidden by a per-metric veto. These are engineering screens, not population confidence estimates.

## Cooperative reasoning cap
Frontend-only opt-in `STRATA_REASONING_NATIVE_CAP=1`. Preserve reasoning/output budgets and existing closing text; end a native segment naturally at the reasoning boundary instead of STOP-draining an oversized request. No native math or cache-state rollback.

Fresh 8K dependency-order A/B/B/A:
- Task wall:128.465234 /103.231548 /103.478128 /128.558937s.
- Pooled reduction19.5758%, both pairs positive.
- All hidden14/14, identical repaired file and completed tool work.
- First four delivered turns match; matched patch turn68.717707->60.260323s (12.3074%,8.457384s).
- Continuation reread3095->19tokens; PP9138/9104->132/132ms.
- Later reasoning/final output differs:6081->5129tokens. Entire task reduction is NOT equal-token native acceleration.
- Both variants retain a known inaccurate explanation about duplicate task emission; no new material false execution/completion claim.
- Original resolver nontrigger regression matches all delivered semantics/work,1213outputs,5/5hidden.

Source admission hardening excludes non-neutral/malformed repetition/presence/frequency penalties, since native penalty history can select serial decoding. This is six additional host-only eligibility lines; the measured penalty-free execution path is unchanged. **360 CPU tests pass**, including347 existing server/accounting tests and13 cap tests. No 8K qualification result is attributed to the hardened hash; the later 64K development pair and native boundary smoke used the hardened source.

The exact three-file source/test/report tree is published on branch `rnd/cooperative-reasoning-cap-20261025`, commit `ea76c1c576fa0f62a3d3c866c363b5470e24053d`. The local equivalent-tree commit is `50bfca6ec62ab8d91b73ecc53698a07c9583ebab`. Main was not changed. Exact-head CI had no reported statuses, runs or checks; this is not a CI-pass claim.

## Separate 64K development pair — not qualification
Actual initial context65532tokens, same tools/budgets/reasoningON:
- A200.321170s,5549outputs,9calls,7turns.
- B189.150547s,5377outputs,8calls,6turns.
- Both visible3/hidden14 pass. Repair source differs only by three consistent local variable renames, but exact patch bytes and completed tool work differ.
- Continuation cache mechanism repeats: reread3095->18tokens, PP10.284->0.184s.
- Cold PP worsens91.530->95.631s in B; retained.
- B final repeats duplicate-emission misconception absent from A final.
- Two fixed processes only. Descriptive wall reduction is not matched-work, quality-equivalence, or 64K performance qualification. No extra arms/retries.

## Reasoning-OFF viability, retained separately
Dependency-order task failed within the unchanged12-turn budget: final visible tests fail after an unnecessary second edit, no final hidden-oracle completion. A first attempt had a sandbox cold-directory initialization failure; that infrastructure issue was fixed and retained separately before the quality failure.
Independent simpler resolver OFF pilot passed5hidden cases, but does not erase dependency-task failure. Both used true template-level disable, zero emitted reasoning channels/tags, not hidden reasoning text. User restored ON; no further OFF runs.

## Parked candidates and closed false leads
- Short-context HC clone: exact component improvement but roughly98ms task exposure, retained as a small potential bundle ingredient, not a model qualification.
- Cached J24 MMQ: exact components but density-dependent mixed timings; no blanket selector promotion or native task qualification.
- Larger short-read cutoff: changed exact state/trajectory despite task success; parked.
- Resident decode down-NT2 resource reduction: exact but effectively flat timing; not revived.
- Existing fused SwiGLU and several converter/guard/cache variants have retained low-gain or negative historical results; no blind repeats.
- Current Service `done.timings` already aggregates retained native-segment PP/TG/generated/drafts. First-segment input/cache fields are intentional; `engine.last` is final GEN. No unnecessary aggregation patch was made. Physical failed-attempt provenance would be a separate optional contract.

## Scope and evidence discipline
Fresh comparisons, fixed budgets, independent external oracles, preserved failures and interrupted blocks, one GPU owner/job, no repeat-until-pass. Model startup is recorded separately from task wall. Nested timing scopes are not added together. Source and raw evidence remain privately retained; this summary contains no raw logs, weights, credentials, host addresses or private paths.

Small-cap CPU coverage and one fixed nine-call native smoke are complete: all 22 emitted IDs matched the frozen reference. Cap1/2 continuations exercised direct live-prefix reuse; cap3/4 restored a previously parked longer prefix. Accepted T2 overflow was exercised; native EOS-at-cap was not. These are bounded protocol checks, not a performance or full-state proof.


## Explicit correction: prefill_pipe=0 does not disable overlap
Earlier communication conflated the INFO field with disabled two-GPU prefill overlap. That interpretation was wrong. Current source already overlaps successive chunks through the successor worker and double handoff buffers; prefill_pipe selects chunk planning/sizing, not the basic overlap mechanism.
The current planner/handoff blocks are byte-identical to the retained earlier source assessment. Pipe1 leaves4096-token chunks unchanged; short cached segments below512 cannot split. More aggressive splitting can change arithmetic shapes, stream-all eligibility and traffic, so this is not a free scheduling-only speedup.
Measured timings and token results remain valid. No flag experiment was run. Sealed historical evidence was not rewritten.
The published HC README reports actual prefill_pipe=0 and makes no overlap claim; it does not assert overlap is disabled.

## Cold PP timing provenance
Native prompt_ms is host-inclusive through request cache restore, loan/read/refill and checkpoint work. Model load and initial Prefill/BLAS handles are initialized before READY and lie in separate startup time. Lazy first-use or shape capture may occur later, but retained clean logs do not establish their cost.
Eligible wide dequantization also bypasses repeated scalar device-attribute queries. That is repeated dispatch work, not only first-use initialization; its cost was not isolated from the kernel change.
Retained clean census contains busy/VRAM/container state, not GPU-clock/temperature or CPU-load time series. The observed cold-PP spread therefore has no established cause. Do not label it thermal or hardware noise, and do not subtract real cold cost.

## Sampled baseline viability — 22:25 UTC checkpoint
Reasoning remains ON. A separately frozen sampled cohort uses temperature1, top_p0.95, top_k20, min_p0 and neutral penalties, with seeds12345/23456/34567 declared before outcomes. The first seed passed both tasks: resolver52.225159s,1624outputs,8tools; dependency-order101.615989s,4722outputs,9tools. External hidden oracles passed5/5 and14/14. These are baseline viability results, not greedy speed comparisons or seed-population estimates.
Neither first-seed task reached the reasoning wrap; dependency patch reasoning ended naturally at2996tokens below3072. Minor dependency-task explanation errors remain, so repair correctness is not prose perfection. The four remaining fixed-seed tasks are pending at this checkpoint; none will be dropped or retuned after outcomes.
The sampled profile deliberately leaves cooperative cap unset and is ineligible for its current greedy-only guard. The controlled4096-output/3072-reasoning policy is not evidence of actual client request limits or overrides; larger output allowances can imply much larger default reasoning budgets. No production/client settings changed.
