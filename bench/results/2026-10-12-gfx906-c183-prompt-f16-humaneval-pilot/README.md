# gfx906 c183 prompt-F16: first-16 HumanEval pilot

**OFF and ON both pass all 16 tasks on base and base+extra tests.** There are no failed/timed-out task statuses or paired outcome regressions/improvements. Six solution texts differ despite identical outcomes.

This fixed pilot covers **HumanEval/0–15**, one greedy completion per task per arm, using the original c183 binary and existing `HIP_PROMPT_F16=0/1` option. Each arm uses one fresh engine and 16 serial requests, thinking disabled, effective cache zero and a 768-token cap. All **32 completions stop naturally**; no retries. Serial reset is not proof of fresh-process equivalence between requests.

The pinned dataset contains **63 base + 11,151 extra inputs**; both arms passed every selected task using the [EvalPlus evaluator](https://github.com/evalplus/evalplus/tree/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e) in CPU isolation. Independent actual audits bind all 32 evaluated solution strings to admitted samples. Generation cleanup passed at **49 C**, API stopped; evaluator cleanup and descendant drain passed. Hashes and aggregate details are in [metrics.json](metrics.json).

Earlier infrastructure failures remain separate: setup native-extension mapping; generation archive-member cap (**zero requests**); evaluator reference-cache file-size cap (**zero generated-solution tests**). Minimal V2 corrections produced this result without task/scoring changes.

This is **16 of 164 tasks**, not full-benchmark or broad-quality qualification. No speed claim follows. [Prior trajectory divergence, USER-text likelihood drift and bounded copy/needle results](../2026-10-11-gfx906-c183-prompt-f16/README.md) remain intact. Exact c183 stays the default; approximate F16 remains experimental. No promotion or implementation PR. Solution contents remain private.
