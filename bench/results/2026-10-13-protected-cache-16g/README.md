# Protected cache anchors with a 16 GiB optional-cache ledger

This directory preserves an opt-in runtime experiment against the exact historical `74aa76d4…` executable/source lineage. It is separate from the existing six-checkpoint spread retention work in PR #1959. The protected design retains absolute coverage anchors independently of two recent heads and places all instrumented optional cache owners under one pre-allocation budget.

## Verified v1 status

- CPU host build: **PASS**. The original baseline binary was reproduced byte-for-byte, eight production host compilations completed, four CPU test executables passed, and no GPU kernel translation units were compiled.
- V1 candidate binary: `7b00d34c85181a2023862e01a5782c68c0403ba5b13a0e0eeec7280afa06b0e6`.
- GPU v1 paired replay: **COMPLETED, ACCEPTANCE FAILED**. Inputs and comparable output IDs matched; decode-anchor reuse, cancellation recovery and accounting checks passed. Compaction read reduction was zero because the baseline fixture did not reproduce historical root fallback. Six ordinary short turns were 5.26% slower in wall time.
- Deployment: **NOT DEPLOYED**. The baseline API was restored and separately verified healthy. A stronger stress fixture and copy-overhead investigation remain open.
- Mainline integration: **NOT DONE**. This is a preservation bundle, not a patch validated against current main. Do not apply its historical runtime patch blindly to the enclosing branch.

The proposed preservation parent is `236a6aac2da7c2df00b1510f8fe46270917e2334`. That identifies where to store this record; it is not the source baseline to which `runtime/protected-cache.patch` applies. Exact input and output hashes are in [source-pins.json](source-pins.json).

## V2: test gate passed, deployment on hold

[V2](runtime-v2/README.md) removes only the unconditional request-end snapshot copy while preserving due protected anchors and live/parked state handling. It explicitly trades away optional off-grid completed-request snapshots. The larger protected-bank parking cost remains. V2 host build passed: eight host compilations, five CPU tests, baseline reproduction and cleanup. Its binary is `2cbcd0eafb1385e4a345bb405e8c677e9fb77f3cbba46088d04c760fdd246ef2`. V2 completed the strengthened 20-request test with matching inputs/outputs and compaction read 123414→33302 (prompt 195967.1→60340.3ms). Deployment is **ON HOLD**: ancestor-return prompt time regressed 962.7→82993.6ms after reuse fell 148544→100786. The successful test gate allows optional ancestor eviction and is not deployment acceptance. V2 was not deployed. See [the full v2 result](evidence/replay-v2/summary.json).

Upstream compatibility review identified a blocker: the historical parking path lacks current-main shared-prefix pins, and its global eviction would bypass pin-aware victim selection. This patch is not directly applicable to current main. See [UPSTREAM.md](UPSTREAM.md); publication is preservation/results only until a real current-main port is implemented and tested.

## Read and reproduce

- [REPORT.md](REPORT.md): failure analysis, retention design, scope and remaining gates.
- [MEMORY.md](MEMORY.md): what the 16 GiB ceiling includes, and what it cannot guarantee.
- [BUILD.md](BUILD.md): exact historical ABI closure, build evidence and reproduction requirements.
- [VALIDATION.md](VALIDATION.md): CPU results and the 13-request paired GPU test plan.
- [ROLLBACK.md](ROLLBACK.md): activation and rollback limits.
- [evidence/cpu/summary.json](evidence/cpu/summary.json): machine-readable verified CPU result.
- [evidence/replay-v1/summary.json](evidence/replay-v1/summary.json): failed GPU acceptance and the individual passing/failing gates.
- [runtime/protected-cache.patch](runtime/protected-cache.patch): exact original runtime patch, with new helper headers also available separately.

Run the self-contained public CPU checks with:

    python3 -B tests/run_cpu_tests.py

These metadata, ledger and protocol tests do not load a model or exercise the GPU. The public protocol rerun uses generated synthetic token IDs, not the private replay seed. No prompts, prompt IDs, host home paths, private host routes, credentials, model weights or executable binaries are included.
