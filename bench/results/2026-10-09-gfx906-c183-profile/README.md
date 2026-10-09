# Current c183: control/profile diagnostic

Date: 2026-10-09 UTC. Status: **completed; diagnostic evidence only**.

The fresh control measured **646.453806 prompt tokens/s and 53.807512 generated tokens/s**. The instrumented process measured **636.884614 and 50.751358**, respectively. Both used the same existing frozen c183 executable. No optimization patch, model rebuild, promotion or deployment was part of this refresh.

## Recipe and observed changes

One control process was followed by one profile process, each serving the identical 65,536-token request and 1,024 greedy outputs. Native arguments and baseline environment values were preserved. The profile added only PREFILL_TIMING, DECODE_TIMING, SPLIT_TIMING and VERIFY_PROFILE. There were no automatic retries.

Crucially, VERIFY_PROFILE disables the main shared fork, which is enabled in this control build. Profiling therefore changes scheduling as well as adding measurement work. Prompt time changed from 101,377.7 to 102,900.9 ms (+1.502500%); decode time changed from 19,030.8 to 20,176.8 ms (+6.021817%). These are observations from one ordered diagnostic pair, not an isolated profiler-overhead estimate, an optimization gain, or a statistically established regression.

All 1,024 output IDs matched between both processes and the historical c183 reference. Engine configuration matched. Available counters nevertheless drifted: accepted/offered drafts were 648/872 versus 648/873, and lookups were 600,000 versus 600,480. Exact IDs do not establish constant work. DONE16 omits optional chain/suffix counters and decode-window count; those fields remain null. The profile's 378 windows come separately from diagnostic stderr.

## Clock validation

The actual timestamp kernel was extracted from the pinned existing HIP object. Its complete 84-byte function matched the disassembly opcode bytes and reads the realtime clock, multiplies the 64-bit value by 40, then stores it. Both devices independently reported a 25,000-kHz wall-clock rate, with all query return codes zero. This supports the 40-ns/tick conversion and millisecond units. Source, object, archive, extracted-image and query identities are retained in [metrics](metrics.json).

## What the profile shows

The primary prefill timeline reports 97,345 ms. Sixteen secondary chunk timelines total 78,145 ms for the same 65,535 prefilled tokens. These overlapping views must not be added. Selected primary intervals are HC read 18,261 ms, expert gate/up 18,193 ms, GDN input 13,987 ms, expert down 10,965 ms and QSA attention 9,424 ms.

Names describe bundled intervals. GDN input includes QKV/gate projections; expert gate/up includes tails and SwiGLU; expert down includes activation quantization. QSA projection also includes post-attention gate/output projection. These figures do not identify independently removable kernel costs.

Decode reports stage totals of 25.21 and 22.29 ms per full window, averaged over 378 windows. The host-timed decode envelope reports 53.38 ms/window, including verify 48.38, draft 4.54 and commit/emit 0.46. GPU stages and nested CPU timers are not an additive whole-model budget.

HC0 “norm” is particularly easy to misread: the stage-0 GDN 0.56-ms interval also includes preceding PLE work. HC1-plus-router includes resident-plan and doorbell-publication work. Neither is an exclusive normalization or HC-kernel measurement.

## Decision and evidence

A 1% throughput improvement would require saving 1,003.739604 ms of control prompt time or 188.423762 ms of control decode time per request, assuming unchanged work. Those are whole-phase budgets, not demonstrated savings. Control window count is unknown; dividing its budget by 378 would mix workloads.

The refresh establishes no newly qualified removable cost. All 22 exported files, raw DONE records, complete stdout captures, termination receipts and ID comparisons were independently verified. Both native processes and the wrapper exited zero. Cleanup passed, power settings were unchanged, and the API remained stopped. Private logs, token arrays and deployment details are excluded here.
