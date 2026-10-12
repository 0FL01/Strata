# Combined HC N4 + peer-affinity qualification

**Both frozen blocks pass for this pinned c183-derived profile.** Pooled PP is **646.247523→672.137076 tokens/s (+4.006136%)**; TG is **53.567198→53.728913 (+0.301892%)**. Mean peer-caller CPU rises **41.475823→74.652695 s (+79.990869%)**, excluding descendants/helpers.

Eight fresh 64K/1,024-output arms use the same binary: A = N4 OFF / affinity OFF; B = N4 ON / affinity ON. Fixed order: A1, B1, B2, A2, B3, A3, A4, B4. All arms are retained.

- **ABBA:** PP **+4.266646%**, TG **+0.521840%**.
- **BAAB:** PP **+3.745738%**, TG **+0.081620%**.
- Each block independently meets PP arithmetic-mean gain ≥1%, both chronological PP pairs positive, and TG arithmetic-mean rate ratio ≥1.0. Pooling does not rescue a failed block.
- **Two TG pairs regress:** B1/A1 **−0.034220% / +6.5 ms decode**; B3/A3 **−0.293685% / +56.5 ms**. This is not a zero-run-loss or statistical-equivalence result.
- Mean native PP+decode falls **3,962.1 ms**; request elapsed falls **3,958.404 ms**. Peer-task wall overlaps PP and cannot be added to these savings. Caller CPU is neither total-process CPU nor energy accounting.

All eight historical output trajectories and recorded work match. Each B arm performs 16 verified mask expansions/restorations and 1,536 N4 takes; persistent censuses match. Independent actual audit: **1,402 checks**; cleanup **53 C**, API stopped.

This qualifies the **combined historical treatment**, without isolating its components or admitting a clean current-main port/default promotion. All [earlier N4 losses](../2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/README.md) and [screening epochs](../2026-10-12-gfx906-c183-peer-affinity-screen/README.md) remain separate. [Metrics](metrics.json) retain every arm, block mean and pair.
