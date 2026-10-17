# gfx906 combined-optimization benchmark kit

Reproducibility evidence for a combined optimization profile on two gfx906 GPUs. Six interleaved pairs completed with exact output and work parity. Results apply to the fixed profile below; they do not establish broad model quality or support for untested backends. Intended repository location: `bench/results/2026-10-17-gfx906-combined/`.

## What is included

- Reviewed v6 runtime helpers: startup probe, short A/C/B smoke, excluded full A/B canary, six-pair driver and native protocol parser.
- Portable standard-library Python tests using CONFIG.test.json and a fake Docker client; these do not use a GPU or Docker daemon.
- Editable `CONFIG.example.json`, derived from the measured configuration with local host paths replaced by `/ABSOLUTE/LOCAL/...` placeholders.
- The exact synthetic token fixture, `fixtures/prompt-65536.json`: 65536 token IDs, SHA256 `63ce3d4042027a00b2193feab143f1d9443b5c31a863a962ec9543ccb54d9695`. This file must accompany any final kit. Do not re-tokenize prose, regenerate tokens or reformat its JSON: the byte hash is checked.
- Actual qualification evidence plus all 12 scored stdout logs, stderr logs and receipts in `evidence/`. Qualification receipts omit process/container identifiers and original commands. Scored receipts retain their structure with original host paths replaced by editable local-path placeholders. Per-file source and public hashes document sanitization; native timings and work records are unchanged. Exact original configurations and evidence remain separately retained.
- `common-build-prerequisites.patch`, SHA256 `4f9a89b9475a7c656b50e44382a053cd9915a8060ce3b607e109b518db00dbb9`, applied identically to both measured arms. These build fixes are not optimization gains.

## Fixed comparison

A: Niko1221/Strata main `477ac13cbe8e582c20484871ce459d20d82df09d` plus the common build prerequisites. B: the same base/prerequisites plus the combined optimization patch. Source/binary hashes are in `evidence/identities.json`. Build both with matching compiler, ROCm libraries, dependencies, architecture flags and release settings; enable the candidate's two optional HC build targets. Enabling a build target does not enable its runtime route.

Hardware/profile: two physical gfx906 Radeon Pro VII 16 GiB cards, Xeon AVX2; context 262144, int8 KV/resident 32768, prefill 4096, split 27, expert-cache request 9900, pool 15, PLE RAM, spec 6 / MTP 4, suffix 0, reserves 1200/1300 MiB. Actual startup: total 18018 expert slots, primary 9399, total 23753 MiB/primary 12391 MiB cache. Freeze the exact profile and verify both arms match. A different actual layout is a different configuration, not automatically this result.

Use the current Q8_0 PLE second shard despite the unchanged filename; historical IQ4_NL measurements do not apply. Both shard identities and the pinned Q8_0 PLE source revision are recorded in evidence/identities.json; the 17-file runtime asset hash inventory is also included. See BUILD.md for post-benchmark collection timing and the historical pack-metadata caveat. Model weights, expert pack/profile, tokenizer and MTP assets are not bundled. The recorded image SHA is a local content identity, not a downloadable image reference; the exact image has not been published; verified source/build commands are in BUILD.md.

Both arms share every common upstream opt-in. Only the seven new component controls differ in `treatment_environment`. `STRATA_ROUTE_TAIL_SKIP=0` explicitly selects full routed work; these measurements are not a comparison with upstream's approximate default 7. Use only the explicit nonsecret environment allowlist. Never copy deployment environment files or credentials into the config/container. `STRATA_API_KEY` is rejected/unset.

Each full request uses the frozen 65536 IDs and 1024 outputs, greedy temperature 0 / top_p 1 / top_k 1 / seed 12345, with an impossible EOS override to force length finish. Short smoke uses its first 4096 IDs and 256 outputs. All measured arms are fresh processes, with no prior GEN request; OS page-cache state is a separate condition to document.

## Run locally

The measured image used AMD clang 23.0.0git, CMake 4.4.3 and GGML revision 3cf03257f219afbe7334045ff7c6a06ac68c627d. Its LLVM directory is labeled `core-7.14`; no unified ROCm release number was verified. See `BUILD.md` for exact compiler provenance and baseline/candidate commands. Install Python 3 and Docker with supported ROCm device access. Edit every local path placeholder, supply/build the exact assets/binaries, and verify image/device permissions. Keep diagnostics that change dispatch disabled; establish an idle benchmark host and a fixed memory/thermal policy separately. The scripts do not stop production services or change clocks.

    python3 -m unittest -v
    python3 probe_startup.py CONFIG.example.json results/startup-A A
    python3 probe_startup.py CONFIG.example.json results/startup-B B
    python3 run_smoke.py CONFIG.example.json results/smoke
    python3 run_canary.py CONFIG.example.json results/canary
    python3 run_pairs.py CONFIG.example.json results/scored

Use a new output directory each time. Startup collects INFO/READY then QUIT; it performs no inference. Smoke uses A upstream, C candidate with A's opt-ins, B candidate with new opt-ins enabled. New switches must default off in C. Canary performs one full A/B pair, excluded from scored results. Review actual headroom and graph behavior before scoring; startup success alone does not establish safe memory use.

The scored driver runs six adjacent balanced pairs: AB, BA, BA, AB, AB, BA. It persists logs/receipts/status, serializes cooperating runs with a file lock and uses owner-scoped cleanup. For remote-shell disconnections, launch detached with file logging and inspect the existing PID/status before doing anything; never start a duplicate. SIGKILL/reboot requires manual inspection of the recorded container before retrying.

Require exact output IDs, non-timing DONE work counters, PP positions, successful exit and matching startup layout. Smoke/canary compare INFO including engine; six-pair replay ignores engine/free-VRAM, while the frozen expected-info check still pins engine. Failed/incomplete arms are not evidence of a gain. Diagnose, retain logs and rerun complete affected pairs under a predeclared plan; do not select favorable arms.

## Results: six scored pairs

All 12 fresh-process arms completed in the fixed order AB, BA, BA, AB, AB, BA. Every arm generated exactly 1024 matching token IDs and had matching non-timing DONE counters, prompt progress and layout. Source data, individual receipts, config, status and the original driver summary are under `evidence/scored-six-pairs/`. To recompute the summary offline, run `python3 protocol.py evidence/scored-six-pairs/manifest.json`; this does not use Docker or a GPU.

- Prompt processing (PP): pooled throughput **621.434 → 643.935 tokens/s**. The geometric mean of the six paired speedups is **+3.62505%**, with an approximate 95% paired-log-t interval of **+2.24982% to +5.01878%**. Individual pair gains range from **+1.64302% to +5.19989%**.
- Token generation (TG): pooled throughput **51.2641 → 55.1578 tokens/s**. The geometric mean paired speedup is **+7.59548%**, with an approximate 95% interval of **+7.27287% to +7.91906%**. Individual pair gains range from **+7.16644% to +7.89733%**.

Pooled throughput is total tokens divided by total native phase time. Paired speedup is `exp(mean(log(A_time / B_time))) - 1`; its interval uses the sample standard deviation of six log ratios and a t critical value with five degrees of freedom. These are different estimators: the pooled PP increase is +3.62082%, while the paired geometric increase is +3.62505%. Do not label one as the other.

The PP point estimate exceeds 3%, but its interval's lower bound is below 3%; this does not establish a minimum 3% PP improvement with 95% confidence. The interval is approximate and reflects these six pairs, not every workload or machine. The paired ratio for combined PP + TG time is also reported in the JSON summary; it is a same-work speedup ratio, not a sum of PP and TG percentages.

**The first pair is retained.** Its PP gain is +1.64302%, and all later pairs are retained too. No lower-gain pair was discarded or reclassified as warmup. The preceding full-profile canary is separate, excluded qualification evidence. The available evidence does not establish that any first-pair difference was caused by a specific cache or thermal effect.

## Separate qualification and scope

Startup A/B completed; short 4096-token prompt / 256-token output A/C/B strict parity passed; excluded 65536-token prompt / 1024-token output A/B strict parity passed. Native canary timings remain raw evidence only and are not part of the six-pair estimate. These output checks establish only the tested trajectories, not general model quality.

Component microbenchmarks use different workloads and denominators and are not aggregated here. Label any component speedup separately; component percentages must never be added. No component-removal screen is included in the aggregate estimate.

Runtime coverage here is limited to the tested two-card gfx906 profile. CPU/reference/compile-guard tests do not establish execution on CUDA, wave32 AMD, other ROCm versions or other model profiles. Those hardware/backend combinations remain untested here. A claimed 200K profile would require separate evidence.

## Reproduction limitations and publication checklist

The exact runtime scripts, prompt fixture, observed config and six-pair evidence are included. The exact build scripts, post-run pack/MTP/profile asset hashes and a source/backend coverage inventory are included; see BUILD.md and COVERAGE.md. A verified distributable container recipe remains unavailable. The separate default-HC-options-OFF build and 4096/256 model parity check passed, including every output ID and non-timing work/layout field; it is not a scored arm. The image SHA identifies local image content and cannot be used as a registry pull reference. Model assets are not bundled.

Keep these limitations explicit until the corresponding metadata is supplied. If the final bundle, model, build or runtime profile changes, repeat qualification and the scored comparison. Assembling this directory does not publish it or launch any benchmark.
