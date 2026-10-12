# gfx906 c183: remaining-main-BF16 exposure observer

**HC injection is the largest observed family:** **3,443.181 ms / 864 calls** on the primary owner and **2,671.397 ms / 672 calls** on the peer. Its shape is **N=4, K=10,240, T=4096/4095**. Primary exposure is **3.390%** of the pinned **101,566.7 ms** uninstrumented OFF PP reference; this is a time proxy, **not a predicted gain**.

One c183-derived host-observer run used **65,536 prompt tokens, one output and F16 OFF**, with unchanged kernels and no tensor capture. Same-stream events bracket original Gemm BF16 calls, including host submission gaps, and nest within unchanged inclusive phase timers. **Neither owners nor nested timers can be summed into critical-path wall time.**

Selected main-BF16 interval totals are **7,276.479 ms / 2,624 calls** primary and **4,728.024 ms / 2,016 calls** peer, kept separate. Actual primary PLE-key BF16 uses **16 calls / 65,535 rows / 1,009.402 ms**; PLE value contributes **211.729 ms**. The census excludes already-optimized main HC down/up and standalone MTP prefill.

This identifies **HC injection for source investigation only**. No optimization, exact-conversion or model-quality result follows. Event-pair highwater **8/6** stays below the source bound **134**; actual audit and cleanup passed, final maximum **54 C**, API stopped. [Metrics and evidence hashes](metrics.json) retain aggregate counts and scope limits.
