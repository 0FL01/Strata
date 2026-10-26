# Agentic quality diagnostics and retained repeat variation
CPU-only analysis, no new model or GPU run.

## Conservative alpha-only diagnostic
The helper parses but never executes one fixed-signature order_tasks(tasks, dependencies) function. It preserves public names, free names, constants, attributes and operators while canonicalizing function-local bindings. Unsupported scopes, reflection and unreviewed calls return UNKNOWN. ALPHA_ONLY_MATCH means restricted AST structure differs only by local renaming; it is NOT a general semantic-equivalence proof or substitute for external hidden behavior tests.

Nine CPU tests pass. The retained64K repair pair differs only in flagged/missing_seen, adj/unlocks and unique/unique_edges, and is classified ALPHA_ONLY_MATCH:
- A SHA256 a5927a6c418c36597b265bbf040d192a93f2966f52070016ccffe1f89e1bf99d
- B SHA256 c41aac4182095cc3d7874cd8d0bf314422fa19b61f53b031c50b20a876e30a88

The old exact-byte/tool-work/prose expectations remain unmet. This diagnostic does NOT retroactively change the64K development verdict.

Run: python3 -B test_alpha_diagnostic.py
Compare: python3 -B alpha_diagnostic.py LEFT.py RIGHT.py

## Retained within-variant repeats
Each row is its own pair, n=2, with identical delivered trajectory and recorded native prompt/reuse/read/generated counts within the pair. Draft accepted/offered count vectors also match within each pair; this is not exhaustive device-work identity. No controls/candidates, contexts, tasks or screens are pooled. Pilots, observers, interrupted runs and resolver nontrigger regression are excluded.
Relative pair span =100*(maximum-minimum)/mean. This is descriptive spread, not significance or a universal noise floor.

| Group | Task wall span% | First cold PP span% | Total native TG span% | Startup span% |
|---|---:|---:|---:|---:|
| resolver wide 8192 A | 1.136 | 3.122 | 0.242 | 3.853 |
| resolver wide 8192 B | 0.697 | 1.067 | 0.059 | 13.329 |
| resolver wide 65536 B | 0.503 | 0.602 | 0.040 | 5.889 |
| resolver wide 65536 A | 2.788 | 4.309 | 0.533 | 17.722 |
| jobgraph wide 8192 A | 2.680 | 18.048 | 0.111 | 3.949 |
| jobgraph wide 8192 B | 0.426 | 0.402 | 0.602 | 13.329 |
| jobgraph reasoning_cap 8192 A | 0.073 | 0.197 | 0.087 | 0.015 |
| jobgraph reasoning_cap 8192 B | 0.239 | 0.510 | 0.288 | 17.968 |

The old jobgraph-wide control cold PP varied17.119->20.515s (18.048%), while its total TG varied91.790->91.892s (0.111%). Both values are retained. Fresh cap controls are much tighter, but that does not make their spread a universal error bar. Startup can vary independently and is outside the defined loaded-model task-wall metric.

Cold prefill is real work and is not subtracted, warmed away or normalized out. Integer-ms native PP/TG scopes are nested diagnostics, not quantities added again to task wall. The retained data cannot establish why cold PP varied (initialization, clocks, scheduling or other causes).

## Prospective interpretation, not a new frozen gate
Future task-quality rules can distinguish successful contract-compliant repairs from byte identity, and harmless local renames from changed algorithms. Keep hidden behavior oracles, exact source hashes/diffs, complete tool execution and prose-accuracy checks. UNKNOWN is not an equivalence pass.
Natural tool-step/output changes may be legitimate closed-loop task outcomes, but cannot be reported as equal-work native acceleration. Any new acceptance rule must be frozen before a new candidate comparison; old gates/results remain intact.

No engine/frontend code, GPU settings, benchmark budgets or selected baseline changed. This branch is local-only while external publication approval is pending.
