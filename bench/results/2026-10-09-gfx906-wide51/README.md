WIDE51 selector replay result
9 October 2026

Decision

Park WIDE51. Correctness passed, but the bounded real-200K replay measured only 1.65% and 0.59% lower isolated selector latency on the two physical gfx906 GPUs. These small component gains do not justify prioritizing model integration. This is an engineering prioritization decision; the experiment had no predeclared speed threshold. No model throughput or tokens-per-second gain is claimed.

Measured result

The figures below are the means of two run medians per arm, in milliseconds per selector call:

GPU 0: baseline 0.476110980; WIDE51 0.468234718; reduction 1.6543%, or 7.876262 microseconds.
GPU 1: baseline 0.464180082; WIDE51 0.461446330; reduction 0.5889%, or 2.733752 microseconds.

On each GPU, both candidate run medians were below both baseline run medians. One ABBA sequence per GPU is insufficient to claim statistical significance or establish a broadly repeatable speedup.

Method and correctness

Two binaries linked the unchanged replay consumer directly against the reviewed baseline FIT17 and candidate WIDE51 selector objects, with no support archive. Both enabled FIT17; only the candidate enabled the exact WIDE51 flag.

Four fresh correctness processes completed before timing: baseline and candidate on each capture's original physical GPU. Then each GPU ran one fresh-process baseline, candidate, candidate, baseline sequence. Each timing process used four warmup graph launches and seven event-timed samples of 64 repeated selector calls. All 56 latency samples were independently reconciled. The correctness processes' incidental timings were excluded.

All 12 processes passed direct production, reference and captured-ID equality, graph replay equality, output padding and end-canary checks, and unchanged-input checks. The two actual 200K capture files passed the unchanged strict validator and CPU exact-ID analysis. Their producer's paired control and diagnostic runs matched requested output IDs and all available counters. No 64K substitute was used.

Supporting evidence

The resource review found all 13 original kernels byte-identical and one new guarded specialization. Scratch fell from 1,048 to 852 bytes per lane; reported occupancy stayed at four waves per SIMD. Resource savings alone did not establish a speedup.

The preceding boundary qualification passed 42 processes and 1,212 graph-transition cases. Source, object, consumer, build, resource, boundary and capture hashes were bound into the replay evidence. Independent reconciliation verified all 37 replay receipt files and all 20 replay-build artifacts.

The replay used sequential processes, fixed 190 W power caps and high performance mode, cooldown and thermal monitoring. Recorded settings were unchanged at completion, cleanup passed, and the API remained stopped. No candidate promotion occurred.

Limits

This measures warm-cache isolated selector latency, including guarded no-op launches, using two private captures from one observed window. It does not cover all query widths, layers or workloads. Dispatch labels are source-expected, not directly traced. Scorer time, end-to-end model time, prompt processing and token generation were not measured. Capture payloads remain private. Cleanup and telemetry statements refer to the recorded experiment, not a current host inspection.
