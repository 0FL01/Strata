# HC BF16 N4: reverse-block TG loss and length checks

**The reverse BAAB block has a 1.612671% TG loss**, ratio **0.983873293**, below the earlier **0.99** tolerance. New paired losses are **−0.361075% / −2.864378%**, adding **68.8 / 559.9 ms** decode time. All four original/new TG pairs are negative; **zero TG loss is not demonstrated**.

PP still improves: new BAAB **+2.645645%**. The [original ABBA](../2026-10-12-gfx906-c183-hc-bf16-n4-model-abba/README.md) remains unchanged at **PP +2.776349%, TG −0.110912%**, with its original qualification. Pooling all eight arms gives **PP +2.711000%, TG −0.862031%**, and **+167.725 ms** mean decode time. Pooled averaging **does not erase the unfavorable reverse block**; new/pooled comparisons are descriptive.

All eight 64K/1,024-output trajectories and available work counters are historical-exact; every arm is retained. Each ON arm takes **1,536 candidate calls**. Sparse inferred-phase telemetry cannot identify the slowdown's cause; CPU and exact phase timings are absent.

Separate single OFF/ON length pairs pass output/work exactness:
- **4K/1,024:** PP **+2.619404%**, TG **+0.110076%**; 96 candidate takes.
- **200K/256:** PP **+2.353601%**, TG **+1.081334%**; 4,608 takes plus **96 baseline tail fallbacks**. Raw T0 denotes source-derived T3391; the ON reference-output mode marker does not override fallback behavior.

Length timings are descriptive, with no new performance gate. Actual audits pass **669/722 checks**; cleanup passes at final **54/55 C**, API stopped. [Metrics](metrics.json) preserve every block and provenance. Pinned opt-in scope only; no universal exactness, broad-quality or default-promotion claim.
