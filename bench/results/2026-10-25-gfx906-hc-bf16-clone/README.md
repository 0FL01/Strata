# gfx906 HC BF16 clone: native screen and baseline selection

Date: 2026-10-25

## Scope

The clone targets terminal BF16 HC prefill GEMMs at T = 4096 or 4093:
down N = 320, K = 10240; up N = 10240, K = 320. Existing successful
F16 dispatches and guard decisions are unchanged. Component correctness
covered 68 cases on both cards; component timing is not a native wall forecast.

The published wiring selects this path by default on gfx906, with
`STRATA_HC_BF16_CLONE=0` as opt-out. **The measurements below used explicit
opt-in `STRATA_HC_BF16_CLONE=1`, not the promoted default wiring.**
Default/opt-out wiring was separately checked as described below; no new
model trajectory was run for that packaging change.

## Fixed native ABBA

One matched main/clone/clone/main screen ran the complete five-request
trajectory, including cold 64K prefill and cached continuations generating
1K and 4K tokens. All **24,584 generated token IDs across 20 requests**
matched exactly. Each process retained 24 graphs; each enabled process
recorded 2,057 successful clone dispatches. Work and runtime-map checks passed.

All profiling/timing observers were off; only event-free per-run dispatch
receipts were added. Actual native INFO reported `prefill_pipe=0`; no
pipelined-overlap claim is made.

Cold-PP throughput gains were **2.3042% and 2.1901%** in the predefined pairs.
Descriptive pooled throughputs and mean latencies:

| Phase | Main PP tok/s | Clone PP tok/s | Main TG tok/s | Clone TG tok/s | Main TTFT ms | Clone TTFT ms | Main call wall ms | Clone call wall ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cold 64K | 679.255 | 694.519 | 68.9305 | 68.8658 | 96514.47 | 94393.98 | 111343.59 | 109236.96 |
| Cached 1K generation | 75.147 | 74.913 | 61.1639 | 61.1469 | 1668.72 | 1673.62 | 18384.70 | 18394.15 |
| Cached 4K generation | 81.967 | 82.211 | 68.6031 | 68.6590 | 1702.12 | 1697.58 | 61382.13 | 61328.97 |

Cached PP throughput uses actual newly read work, 123 and 137 tokens,
respectively, not generation length. Pooled figures do not replace paired gates.

## Preserved result and subsequent decision

The frozen screen required at least 1% cold-PP gain in both pairs and zero
regression in every pair's cold/cached TG, TTFT and call wall.
**The strict screen failed.** Cold TG declined about 0.094% in both pairs.
Cached-1K TG declined 0.030% and 0.026%, TTFT increased 0.408% and 0.179%,
and call wall increased 0.064% and 0.039%. These small differences fail the
literal rule but do not establish causal harm or statistical significance.

The historical outcome remains correctness PASS and strict performance-screen
FAIL. Subsequent baseline selection is an **explicit user-selected override**
accepting the observed tradeoff, not a retroactive PASS, relaxed threshold,
or automatic qualification.

No 8K qualification, agentic-workload benchmark, repeated-until-pass trial,
or broader performance claim is supported. Build verification distinguishes
exact executable device code/data from an explicit compiler CUID-name/hash-
metadata exception; raw device-image byte identity is not claimed.

## Publication build verification

Hardware: two AMD MI50 (gfx906) GPUs. Measured base commit:
`2fea96969e5947bfc0019169d4b5296e8d8a96f5`.
Measured opt-in binary SHA256:
`175571a7938226572e4f9738bcd32b22b3917c78e019f4f699c1e2e41d048628`.

The gfx906-only object is compiled as HIP C++17 with effective `-O2 -fno-fast-math`.
Its 1,788 kernel instruction bytes and 64-byte descriptor match the admitted
component exactly. All 136 unaffected linked objects are unchanged.
Original device code/data/descriptors are unchanged. The compiler-generated
CUID rename changes symbol ordering and lookup/relocation indices; resolved
symbol attributes, all four relocation targets and both hash tables were checked.
This is a narrow semantic metadata exception, not raw device-image identity.

The default selector is enabled for an unset variable or exact `1`; exact `0`,
empty and invalid values disable it. CPU selector/provenance tests passed in
both gfx906 and CPU-only configurations. Unsupported device architectures fall
back; genuine HIP/device errors retain their fatal checks.
`-DSTRATA_GFX906_HC_BF16_CLONE=OFF` excludes the object and hooks and rebuilt to
the exact prior executable SHA256:
`f13a4600eb1da93515b9ddac689e97b2839896deaf64fbf2632cfe08913bc096`.

The default-enabled publication build SHA256 is
`04761771491379c012b29bbc969628339cc0c98bf0cd7471277acf5bf6872176`.
This was an incremental build with verified retained-object reuse, not a clean
full rebuild. CUDA, RDNA HIP and SYCL builds were not run; the new object is
excluded outside the gfx906 compatibility backend. No service was started.
