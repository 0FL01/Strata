# Empty-PCIe elision: technical PASS, performance FAIL

**Do not promote.** Default-OFF, release-local R&D on engine 0.1.42 (`61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`). The idea was to omit only the mode7/fused-SwiGLU PCIe grouped call when the admitted production planner guarantees zero groups, preserving waits, plan visibility, CPU copy/zero, hit-add and joins. The [prior observer](../2026-10-11-gfx906-v0142-empty-pcie-observer/README.md) motivated source review; its local brackets do not predict removable time or model speedup.

## Tested and why it failed

On 2026-10-11, 05:33:22–05:47:32 UTC, eight fresh processes submitted twelve requests: eleven completed plus the expected positive-share refusal. QBASE (pristine release) and candidate QOFF/QON each repeated the same cold 4K fixture with 128 then one output. QNEG completed a zero-share request, then refused the positive-share request before further prompt/verify work. Candidate-only **A1/B1/B2/A2** used OFF/ON/ON/OFF with **65,536 input / 1,024 output** tokens, without trace/observer/VERIFY_PROFILE instrumentation. Query swizzle/reduce12 stayed ON; lane-cell stayed OFF.

| Arm | PP ms | TG ms | PP tokens/s | TG tokens/s |
| --- | ---: | ---: | ---: | ---: |
| A1 OFF | 104630.6 | 20042.7 | 626.355961 | 51.090921 |
| B1 ON | 104742.7 | 19960.7 | 625.685609 | 51.300806 |
| B2 ON | 104682.3 | 19709.9 | 626.046619 | 51.953587 |
| A2 OFF | 106293.5 | 20038.9 | 616.556986 | 51.100609 |

| Metric | OFF mean | ON mean | Mean gain | B1/A1 | B2/A2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| PP | 621.456473 | 625.866114 | +0.709565% | **-0.107024%** | +1.539133% |
| TG | 51.095765 | 51.627196 | +1.040069% | +0.410807% | +1.669212% |

Rates use actual tokens/native milliseconds ×1,000; means are arithmetic means of rates. The unchanged gate requires a winning mean ≥1%, both winning pairs >0, and companion mean/pairs ≥0. **TG's mean passed its threshold, but the negative PP companion pair fails qualification.** Every arm remains included, with no causal attribution for A2, dropped pair, timing retry, threshold adjustment, deployment or upstream PR.

## Correctness, failures and limits

- All **4,611 completed output IDs**, available work and INFO capacity matched within their predeclared comparison groups. Timing arms all had accepted/offered **678/862**, prompt reuse0 and cache hits/lookups548429/569246. QON refreshed both-owner admission for each request; first-request construction covered T1/4/2/3 on both owners, while the one-token repeat reused graphs without new construction records. Traces are host construction evidence before EndCapture/instantiate/upload, not replay counts or saved time.
- Component V1 failed CID startup publication after **89 partial GPU0 records**; GPU1 never launched. It was not a component PASS. Corrected component V2 passed **1,480 records**, 740/GPU (120 zero,20 nonempty,200 sequence cases and600 captured replays per GPU). The current component admission explicitly reuses that historical hardware run through exact binary/input identity; it is not new hardware execution.
- Native V1 failed missing device0 construction evidence after five completed requests/386 IDs; its early-owner return bypassed the logger. QNEG and timing never ran. V2 adds exactly three logging lines before that return; device sources remain unchanged and strict owner coverage remains required. V1's misleading reporting label and failed prefix-persistence behavior remain documented in metrics.
- All eight arms left STRATA_ROUTE_TAIL_SKIP unset and reported **default7 ON**. Parity is within this shared tail-skip-enabled release profile, not tail-skip-disabled/exact-no-tail reference semantics.
- Static proof preserves exact original instruction/descriptor/constant/metadata bytes across61 images; **whole-device-image equality is false** because of explicitly accounted CUID/table differences. V2 device bundles and component executable are raw-identical to V1. Selected host CFG proofs are not whole-program equivalence; full compiler/vendor/preprocessor/static-archive bytes were not exported. CMake attempted discovery, so zero discovery calls is not claimed.
- Cleanup passed; API stayed stopped. Edge/hotspot maxima were59/80°C; final sensors≤50°C. High mode/configured190W caps stayed unchanged; instantaneous readings may exceed the cap. Samples were not stage-synchronized and explain no timing variation. Narrow gfx906 mode7/phase0, fused, geometry2560x640,27/21 split,K10/G1, known serial dispatch and zero effective integer PCIe shares only. No positive-share optimization, mode8, invalid plans, general fault recovery, cross-release gain or production qualification.

## Evidence

[metrics.json](metrics.json) preserves exact rates, all arms, failed stages, historical rebind, test scopes and provenance hashes. No private host paths, PIDs, credentials, raw prompts or model payloads are published. Static V2 audit SHA-256: `712d2ec5314c7019c10cb7c7d0f796cedbf849a3b1431b0cd0aa3d1d425567de`. Native V2 archive: `ad241bbfdd51ad48bf800964f4cba7a88644b82feba4b7c381245d5429294f84` (286,597 bytes,118 members,1,995,731 expanded bytes). Actual native audit SHA-256: `08e46e1d4df032463aa9ed9c7e5efec86ba50b589e770ac22c7f26b2c6c72cf8`.
