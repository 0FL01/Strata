# v0.1.42 on dual gfx906: release-local attention validation

## Result and scope

**PASS for the predeclared release-local fixed-work screen.** A clean, unmodified v0.1.42 build passed component parity on both gfx906 GPUs on the MI50 test server and the same-binary full-model OFF/ON screen. Enabling query swizzle and reduce12 together increased mean native-counter prefill throughput by **4.593492%** and token-generation throughput by **1.816550%** on this 65,536-token prompt / 1,024-token output workload. Both forward/reverse pairs were positive, all available work matched, and all full output token IDs matched within each tested prompt size.

This validates the combined flags for this release/model/profile and fixed screen. It is not a speed comparison against c183, an estimate of either flag's individual model contribution, a statistical significance claim, service promotion, or 200K-context qualification. Only two clean observations per OFF/ON arm were collected.

The test server is called MI50; this report identifies the devices by the verified gfx906 architecture rather than inferring board branding from that server name. Earlier qualified reporting records the runtime name AMD Radeon Pro VII.

## Exact clean build

- Strata tag v0.1.42: `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`.
- llama.cpp input: `3cf03257f219afbe7334045ff7c6a06ac68c627d`.
- Source archive SHA-256: `fd23af35cf2d74111dfb8d70f3c4306b2a8479ec2121dcba3dc3b86e4b57dc0b`.
- The initial missing-Ninja preflight failure remains preserved. A fresh Unix Makefiles build completed in **400.811391 seconds** in the pinned compiler image; no source patch was introduced to rescue it.
- Release/gfx906, portable AVX2/FMA/F16C/BMI2, native experts; AVX512/AMX disabled. The build used the project's gfx906 CUDA-compatibility configuration (`STRATA_ENABLE_CUDA=ON`, `STRATA_HIP_GFX906=ON`, `STRATA_ENABLE_HIP=OFF`). Actual HIP runtime linkage and gfx906 architecture were checked.
- The same executable SHA-256 `572c7fb33c95d8b5c16803a8550abeab13eeccb9314136ae101ce61ecd605171` was used for all six full-model arms. The independent build audit checks source integrity, 191 compile commands, native MMQ translation units, AVX2 quantizer compilation, executable outputs, and cleanup. Build success alone was not treated as runtime qualification.

## Component results, separate from model throughput

Production QSA chunk+merge testing compared A (both flags OFF), B (query swizzle only), and C (query swizzle plus reduce12). All **26 full dumps / 16,023,552 bytes** matched exactly within and across the two GPUs, including edge fixtures and the route smoke test. The prior 31-check host mock guard is separate evidence, not 31 GPU tests.

| Device | A paired mean median, ms | B, ms | C, ms | Combined latency reduction |
| --- | ---: | ---: | ---: | ---: |
| GPU 0 | 1.190959 | 1.0376395 | 0.759998 | 36.186048% |
| GPU 1 | 1.1879995 | 1.0319985 | 0.758759 | 36.131370% |

These percentages measure component latency only. They are not model throughput percentages.

## Full-model method and measurements

The fixed order was **QOFF, QON, A1, B1, B2, A2**. QOFF/QON used a fresh 4,096-token prompt and 128 outputs with route traces. A/B used fresh 65,536-token prompts and 1,024 outputs with traces absent. A sets `STRATA_GFX906_ATTN_QUERY_SWIZZLE=0` and `STRATA_GFX906_ATTN_REDUCE12=0`; B sets both to 1. These are the only treatment differences. Sampling was deterministic (seed 12345, temperature 0, top-k 1, top-p 1).

The unchanged gate required at least 1% mean improvement in PP or TG, positive forward/reverse pairs for that metric, and nonnegative companion mean and both pairs. **Both PP and TG gates passed.** Traced 4K durations were excluded from performance.

| Native-counter throughput | OFF mean, tokens/s | ON mean, tokens/s | Mean gain | Forward/reverse pair gains |
| --- | ---: | ---: | ---: | --- |
| PP | 598.744067 | 626.247328 | 4.593492% | 4.554337%, 4.632679% |
| TG | 50.165508 | 51.076789 | 1.816550% | 1.769594%, 1.863596% |

The 4K pair matched all 128 IDs and available work; the four clean arms matched all 1,024 IDs, including the repeated OFF reference. Clean-arm work was accepted/offered 678/862, cache hits/lookups 548429/569246, and suffix windows/accepted/offered 2/3/8. All prompts were cold: full prompt read and zero prompt reuse. Five unavailable optional chain counters remain null, not zero. Full per-arm timings, counters, profile and output hashes are retained in [metrics.json](metrics.json).

The native capacity profile was established from release OFF and checked across arms: 19,078 total / 9,900 primary expert slots, 25,150 / 13,051 MiB expert cache, 32,400 MiB arena, and 15 pool workers. These were observed release values, not imported c183 expectations. The configured context limit of 204,800 does not mean a 200K prompt was tested.

Thirteen legacy setting names absent from the exact release C/C++ sources were cleared. `STRATA_EXP_MODE` still exists, but legacy value 16 has no dedicated release implementation and would take the gfx906 fallback 2; it was omitted to retain release default 7. The removed `STRATA_MMVF_RPB` setting is replaced by the release rows launcher's fixed RPB=4. The full source-backed flag matrix is retained in metrics. Supported common flags do not imply identical behavior to c183.

## Route, safety, and audit limits

The 4K trace showed query active=0 OFF and active=1 ON with kv_mode=1/lane_cell=0; reduce12 selections appeared only ON. Its two records are thread-local host observations without physical-device identifiers. They do not establish every launch/layer or two physical GPU routes. Both-GPU numerical coverage comes from the separate component test.

Actual screen execution was **2026-10-10 17:46:31.264836–17:58:52.310061 UTC**. Within each arm, all 28 persistent thread identities and READY/DONE affinity inventories matched. Peak sampled sensor temperature was 81°C and final maximum 52°C. Reviewed high-mode 190 W device caps and cleanup checks passed; the API remained stopped. No profiler, service deployment, or default-setting promotion was performed.

Independent full-model auditing verified 70 raw files from the 159,315-byte receipt archive. Private logs, model payloads, host paths and process identifiers are omitted from this report. Immutable receipt hashes bind the retained evidence:

- Build audit: `0ceb6319bc6632c9f56ed2aba96564655fc3e8de59df3739f13736ac08e30030`.
- Component audit: `293a01e2f7659fb001421e4e3df932db358f476a3ba450d9d83a94bf43caba34`.
- Full-model audit: `32dd1b61050ce9426853c3bb81a7a8d3655840edf3b7ff7a850ff3243a28c640`.
- Recomputed full-model metrics: `1a558e89b11ed0fd3a25a1a2dd636e88fcc4244f1be3efc717c4014fa03e2132`.
- Full-model receipt archive: `605eaaf2bfc0743579cb9f3830b5ec8446b48b477550130695ee26712ed40ea7`.
