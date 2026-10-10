# v0.1.42 top-k REG2/FIT1: exact results, failed performance gate

## Outcome

**Technical execution PASS; scientific performance screen FAIL. No qualification or promotion.** The release-local combined top-k treatment improved mean token-generation throughput by 2.564108%, with both TG pairs positive. However, its first prefill companion pair regressed by 0.053470%, violating the unchanged rule requiring nonnegative companion pairs. Mean PP improved only 0.113856%. The failure is preserved without a tolerance exception, automatic retry, or rerun-to-win.

| Native-counter metric | OFF mean, tokens/s | ON mean, tokens/s | Mean change | Forward/reverse pair changes |
| --- | ---: | ---: | ---: | --- |
| PP | 625.224197 | 625.936053 | +0.113856% | -0.053470%, +0.281646% |
| TG | 51.083294 | 52.393125 | +2.564108% | +2.480485%, +2.647834% |

All tested full output IDs, available work and capacity checks passed within each prompt-size group. These are two clean observations per OFF/ON arm, not a significance result. The measured treatment combines REG2 and FIT1; neither per-PR contributions nor cross-release gains are inferred. Earlier c183 or attention gains are not added to these numbers.

## Source, build, and default-OFF ISA

The stack was built on release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, with pinned PR #1535 head `ca3533157d066a13b128f3daa61f56411dcf3155` and PR #1743 head `6868ebdfbd13daf3c5fcd6106c15feccc1419d22`. The clean build took 404.878068 seconds. The release baseline executable is `572c7fb33c95d8b5c16803a8550abeab13eeccb9314136ae101ce61ecd605171`; the candidate is `cdf8dffcddc6bc6c84c03cb90567d9c1e71e687af46791f4e46d9d5e4f071185`. The actual selector payload was bound in the engine and all three component drivers.

Default-OFF audit matched all nine existing device code bodies byte-for-byte without instruction normalization. Metadata matched except names, and descriptors except entry displacement; ABI/resources and reviewed dispatch equivalence passed. Added host environment checks mean the candidate executable is not byte-identical to the release baseline, and zero host overhead is not claimed.

The added FIT17 kernel allocates 64 VGPRs and 104 SGPRs, 32,908 bytes of group memory and 56 private bytes; guarded REG66 uses 1,048 private bytes. Spill metadata is retained in metrics. These are not zero-spill kernels. CUDA, non-gfx906 HIP and SYCL were not tested by this campaign.

## Components on both gfx906 GPUs

The independent component audit passed **56 processes**, including exact internal selector-ID checks against reference/CPU/captured inputs, graph transitions and canaries. There were 417 transition case checks per GPU, plus default-OFF public-probe and changed-step graph checks. Actual-engine-linked drivers were pinned and their complete stdout/stderr independently reparsed.

External selected-ID arrays were not retained. Consequently this evidence is internal driver exactness on each device, not a new external dump comparison or a cross-GPU ID-array comparison. Historical captured inputs test selector correctness, not the current model workload. Reused driver destructor return values are not individually attested; checked main operations and owned-container cleanup remain the runtime evidence.

FIT17 incremental isolated-component latency reductions were **26.035077%** and **26.291777%** on the two GPUs. These component percentages do not establish full-stack or model throughput. Per-run medians and the component receipt are retained in [metrics.json](metrics.json).

## Fixed full-model method

Order: **QBASE, QOFF, QON, A1, B1, B2, A2**. The first three were fresh 4,096-token / 128-output diagnostics: pristine release baseline, candidate OFF, and candidate ON. All three matched full IDs/work/capacities. Diagnostic durations were excluded from performance; the 4K baseline check does not establish baseline/candidate throughput equivalence.

The four clean timing arms used the same candidate binary, cold 65,536-token prompts and 1,024 outputs. A used `STRATA_GFX906_TOPK_REG=0` and `STRATA_GFX906_TOPK_FIT17=0`; B used REG=2 and FIT17=1. Query swizzle and reduce12 remained ON in all arms. The validated release profile and deterministic sampling were retained; there were no affinity changes or profiling. All timing traces were absent.

The predeclared rule required at least 1% mean PP or TG gain, positive forward/reverse pairs for the winning metric, and nonnegative companion mean and both pairs. Both combined gates are false: PP lacks the 1% gain and a positive first pair; TG meets its gain/pair conditions but fails the PP companion-pair condition.

All four clean arms repeated the full 1,024 IDs and available work exactly, including OFF repeat. Work was accepted/offered 678/862, cache hits/lookups 548429/569246, suffix windows/accepted/offered 2/3/8, prompt read 65536 and reuse 0. Five unavailable optional chain counters remain null. The three diagnostics matched 128 IDs and their own work reference; no c183 expected data was imported. Capacity was equal across all seven arms, including 19,078 total / 9,900 primary slots, 32,400 MiB arena, and 15 pool workers.

QON emitted one thread-local host topology record: nq=1, capacity_blocks=51202, cap=2051. It establishes enabled guarded host topology only. Device steps choose the actual arm, so this record does not establish FIT17 device execution, physical-GPU identity, or every-launch coverage. Component graph-transition evidence is separate.

## Execution and limitations

Actual execution: **2026-10-10 19:17:52.043328–19:30:38.019625 UTC**. Within each arm, all 28 persistent thread identities and READY/DONE affinity inventories matched. Peak sampled GPU sensor temperature was 82°C; final maximum 51°C. Reviewed high-mode 190 W caps, admission, owned cleanup and API-stopped state passed.

This is a release-local candidate OFF/ON screen on both gfx906 GPUs on the MI50 test server. The server name is not used to infer board branding. No service/default promotion, 200K-context qualification, universal speedup, or regression waiver follows. The configured context capacity is not a tested 200K prompt.

## Immutable evidence

Private paths, process identifiers, model payloads and raw logs are excluded. Metrics retain source/build identities, exact numerical results, limitations and hashes. The actual full-model archive contains 80 regular files (180,113 bytes compressed).

- Build audit: `26cd7ca754b4698763f8dac881c1256314be78da835d3228db0baf64abd12ab0`.
- ISA audit: `80d8dd5467ae324bb818e19cb785e06fffd6244a6eee48ba213fecbfeea1da76`.
- Component audit: `1e5794ed726ba064a188f68fe699f2be7f795f4b41f75556d5c0e13d4655b273`.
- Full-model audit: `60d1b544e768f15a5208046501aff6dbb37bf86997439d293f9c4451ab4f2ef4`.
- Recomputed full-model metrics: `5c370c397b4cbc0c2d9e326e70d4d74fb5878df1e0127ea135d4708bf31bcb9c`.
- Full-model archive: `0af1060ecf8fbe67f7d82f0da0d5cd186b719da2f4c9df2ed0d65fd7df0285ff`.
