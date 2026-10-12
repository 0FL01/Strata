# Joined observer, current-state inventory and peer-affinity screen

**One affinity screen improved PP by 1.504940%, with substantially more peer-caller CPU time: 40.417→74.376 s (+33.958774 s, +84.02%).** This excludes child/helper threads and does not establish useful-compute efficiency or energy neutrality.

The affinity pair keeps HC N4 ON in both arms and changes affinity OFF→ON, at 64K/1,024 outputs. TG changes +0.080068%; native PP+decode falls 1,478.7 ms and request elapsed falls 1,483.786 ms. All 16 PP chunks improve; masks restore and the output/work census matches. Involuntary switches fall 13,923→310; first-15 caller CPU/wall rises 49.612→99.349%. This single pair motivates a separate fixed eight-arm test; it is not qualification.

The preceding **joined-observer V2** pair instead changes N4 OFF→ON. Decode falls only **19.7 ms**; no slow episode recurs, and each shape's maximum is its first window. Its weaker **PP +0.426873%** is retained: the 4,096→8,192 progress interval is **2,139±2 ms slower** ON, while the other 15 sum to −2,561 ms. Nothing is removed from the reported rate.

The read-only inventory finds no current short-window pressure or observed ancestor throttling. It cannot reconstruct removed-container limits or historical pressure. Kernel-log access was denied.

Both experiments use diagnostic instrumentation. Joined thread-CPU brackets have endpoint skew; signed wall-minus-CPU is not scheduler time. Sparse samples cannot identify a unique cause. **The earlier four negative N4 TG pairs and observed stalls remain unresolved.** No stall-removal, zero-loss or default-promotion claim follows.

Actual audits pass (joined 1,128 checks; inventory 29; screen 412), with cleanup/API-off verified.

See [aggregate metrics](metrics.json) and [retained unfavorable results](../2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/README.md).
