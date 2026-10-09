# FIT17: public selector component qualification

## Result and scope

The public selector component completed **54 processes, all exit 0**, on both gfx906 devices. Correctness checks passed. Real-input selector A1/B1/B2/A2 reproduced lower component latency:

| Device | Mean A process median, ms | Mean B process median, ms | Latency reduction |
|---|---:|---:|---:|
| GPU 0 | 0.1907362265 | 0.1416537390 | **25.7331752864%** |
| GPU 1 | 0.1951325085 | 0.1442825200 | **26.0592091451%** |

This is a warm-cache isolated selector measurement on one captured layer per device, including the guarded no-op launch. It excludes the scorer and is neither whole-model throughput nor a full public-tree build. The original 30% discovery gate remains failed and was not redefined. These are reproduction measurements after the separately justified frozen-stack model studies.

## Public source and link boundary

- Public base: [PR #1535 head ca353315](https://github.com/0FL01/Strata/commit/ca3533157d066a13b128f3daa61f56411dcf3155).
- Candidate `qsa_select.cu` SHA256: `5fc5d78c6155fa0987dee751a875ab714516c88209b0938db17699061cc7de1a`.
- Patch SHA256: `aeba2986cfd4086e79d2ef9532af405886a695d2144017ed46159105a6472b2a`.
- Direct public selector translation unit, pinned public headers and harness objects link with system HIP/C++ runtime. **No frozen support archive is used.**
- Six base/candidate binaries are bound by SHA256 in the [numeric receipt](public-component-results.json).

The resource/ISA precheck was recorded before the GPU runs; its source hash is retained as provenance, not treated as the final GPU status. Existing direct device-image disassembly was compared with the qualified private c183 production object, removing address/encoding comments and whitespace and excluding trailing padding. Relative branch immediates and operands were retained; saved compiler assembly was also compared. Matching normalized instructions and resource/ABI metadata do not assert byte-identical complete binaries.

## Correctness coverage

- 8 public parity selftest processes: base and candidate unset/0/1 on both devices, 18 cases each, **144 cases** total. Continuous/quantized/equal-score and adversarial IDs match the reference.
- 30 transition processes: base off, candidate off/on × nq=1/4/6/8/9 × two devices. **834 windows / 4,836 rows** pass CPU/reference/graph ID, padding, canary and input-preservation checks. Each process uses one graph instantiation with constant addresses/capacities, exercising changing steps and threshold/mixed-row cases.
- 8 captured-input correctness processes: base plus candidate unset/0/1 on both devices; production/reference/captured IDs, padding/canaries, unchanged input bytes and graph IDs pass.
- 8 separate timing processes: A1/B1/B2/A2 on each device using the same candidate capture binary, only FIT17 0/1/1/0 changing. Seven batch-64 timing samples per process; FIT17 trace is disabled and timing stderr is empty.

Total: 46 correctness processes plus 8 timing processes. Correctness-suite timings are not used as performance evidence. Raw output IDs are not embedded in this compact public-component receipt; it records per-process check results and stdout/stderr SHA256 values. The previously published full model ID arrays remain unchanged in their separate receipt.

## Timing arithmetic

GPU 0 A medians: 0.190732449 / 0.190740004 ms; B: 0.141629979 / 0.141677499 ms.
GPU 1 A medians: 0.194770008 / 0.195495009 ms; B: 0.144222558 / 0.144342482 ms.

Each process median was recalculated from all seven saved samples and checked against its raw stdout. A and B are means of their two process medians; reduction = 100 × (A−B)/A. Every B process is faster than every A process on its device. Captured geometry: pos0=65536, nq=4, capacity_blocks=51202, cap=2051; this does not establish a general-workload confidence interval.

## ISA and resource caveats

Public scalar, wide, original-control, counted and reference selector instruction/resource evidence matches the tested private production counterparts. Default-off control/counted/reference paths also match the public base.

| Variant | SGPR/VGPR | Scratch bytes/lane | SGPR/VGPR spills | LDS bytes/block | Waves/SIMD |
|---|---:|---:|---:|---:|---:|
| scalar17 | 104/64 | 56 | 44/25 | 32908 | 4 |
| wide66 | 104/64 | 1048 | 539/468 | 32908 | 4 |
| original control66 | 104/64 | 1048 | 527/467 | 32908 | 4 |

Scalar scratch/spills are reduced, not eliminated. The wide path matches tested private wide, not the original control: spills increase by 12 SGPR / 1 VGPR and guard/extra-launch overhead remains.

## Relationship to the model studies

The [model report](README.md) remains bound to frozen private binary c183: fixed-policy TG +1.413177% and default-adaptive TG +1.299911%, with its counter drift, failed gates and limits retained. The public component qualification does not convert those measurements into a public-port model benchmark or establish upstream CI/merge readiness. No full public-engine build, new model throughput result or production promotion is claimed.

## Offline validation

From this directory:

    python3 check_public_component.py public-component-results.json --selftest

The validator recomputes counts, process-mode coverage, seven-sample medians and both ABBA reductions; checks binary/source/ISA identity fields and retained failures; and rejects **16 intentional corruptions**. It checks consistency of this sanitized evidence, not the original binary contents, omitted raw outputs or hardware. Private paths, operational manifests, raw logs and preparation scripts are excluded.
