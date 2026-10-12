# gfx906 c183 prompt-F16: balanced ABBA and option verdict

**Balanced PP throughput rises 23.4639%: 645.255→796.657 tokens/s** (arithmetic mean of two rates per mode). Pair gains are **+23.3093% / +23.6177%**. The frozen criterion, mean gain ≥1% with both pairs positive, **passes** without exclusions.

Four fresh-process runs use the original c183 binary, existing `HIP_PROMPT_F16=0/1`, and one fixed **65,536-token prompt + 1,024 outputs**, in **OFF, ON, ON, OFF** order. Each mode reproduces its output trajectory and available work counters exactly; both OFF runs match historical output. Across modes, first divergence is at **zero-based index 13**, with **986 differing outputs**.

Observed TG means are **53.8658→55.5015 tokens/s (+3.0366%)**, descriptive only: accepted/offered work is **647/868→678/875**, and cache hits/lookups also differ. This is not an equal-work TG speedup.

## Experimental-option verdict

The existing approximate F16 option has a positive balanced PP result on this fixture. [The fixed HumanEval pilot](../2026-10-12-gfx906-c183-prompt-f16-humaneval-pilot/README.md) passes all 16 selected tasks in both modes; [copy sanity and bounded 64K/200K retrieval also pass](../2026-10-11-gfx906-c183-prompt-f16/README.md). Those narrow checks do not erase earlier **USER-text NLL drift** or trajectory divergence and do not certify general quality.

**Exact c183 remains the unchanged default; F16 remains an optional experimental approximation.** No new implementation PR or further GPU run follows this report. Independent actual audit and cleanup passed; final sampled maximum **53 C**, API stopped. [Metrics and evidence hashes](metrics.json) contain aggregates only.
