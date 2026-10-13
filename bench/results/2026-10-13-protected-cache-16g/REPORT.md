# Why protected anchors, and what has been established

This report describes the frozen v1 runtime. The narrow, separately pinned v2 change and its explicit off-grid reuse tradeoff are documented in [runtime-v2/README.md](runtime-v2/README.md). V1 measurements remain attributed to v1.

## The motivating compaction miss

In the recorded request 22, the incoming common-prefix length was 117131. The retained checkpoint at 117170 was 39 tokens too late to restore. The surviving bank was 10674, 117170, 133472, 142574, 146409 and 147644. Only the root at 10674 was eligible, so the engine processed 123414 prompt tokens in 195335 ms; 106457 of those tokens repeated an already matching prefix. The genuinely changed/new suffix was 16957 tokens.

The state at 117170 cannot be made into a valid earlier recurrent checkpoint merely by truncating token/KV arrays. The earlier 84402 and 100786 snapshots had already been evicted before parking could preserve them. This is a retention/capture-coverage problem; it does not justify changing model math or claiming a bad GPU kernel.

With the same recorded creation positions, protecting first-crossing absolute 16K anchors retains 100786, giving 33302 total prompt tokens read: 16345 matching-prefix tokens plus the 16957-token unmatched suffix. That is a host-policy counterfactual, not a GPU timing result. An ideal exact-boundary grid would use 114688 and read 19400 tokens, but the trace contains no snapshot at 114688. The ideal-grid result is not the promise of this implementation. The old 195335 ms value must not be linearly extrapolated into a predicted speedup.

## Difference from PR #1959 and the six-point spread policy

The earlier work improves which entries survive inside a small legacy checkpoint bank, and performs strict ancestor cleanup. This candidate introduces a separate opt-in contract:

1. A persistent absolute target schedule at multiples of 16384 tokens follows the conversation lineage across short requests.
2. Each target is represented by a complete snapshot taken at an existing safe, committed opportunity at or after the threshold. Stored length is the actual evaluated position.
3. The root, all protected anchors and two otherwise-unprotected recent heads are independent retention roles. Recency pressure cannot evict an anchor, and no fallback protected victim is allowed.
4. Captures, parking, selected incoming images, retained KV and temporary ownership overlap are admitted through a shared 16 GiB optional-cache capacity/reservation ledger.

The legacy policy remains selected when the flag is absent. When both spread and protected flags are present, protected selection takes precedence. A new duplicate upstream pull request for the old spread policy is not needed.

## Supported execution and state correctness precautions

The new flag is `--prompt-cache-protected`. The candidate gates its use to the reviewed serving configuration: positive prompt caching, two-GPU split 27 with non-overlapped stage execution, PP 4096, spec 6, context at most 262144, at most four parked slots, and no batch/pipeline windows. Disk SAVE/RESTORE commands are rejected while protected mode is enabled. Vision capability stays enabled in the reviewed configuration, but the text-only replay does not establish image-state parity.

No GPU kernels, PP chunk boundaries, verifier window sizes, draft order, deferred-primary-commit arithmetic or model parameters were changed. The v1 GPU replay later matched its text input/output sequences but failed overall acceptance on zero compaction gain and exposed ordinary-short-turn overhead; it does not establish the original regression fix. See [VALIDATION.md](VALIDATION.md).

Batched prefill captures all participating stage states at coherent existing endpoints. Admission reserves the whole multipart peak before the first stage allocates, and a checkpoint is published only after all stages validate. A stage with zero GDN layers is valid when that stage's actual expected geometry says so. At most two pending positions are admitted.

Serial prompt windows capture after committed verifier input and draft prefill. Decode capture occurs only after the deferred primary commit drains, draft/adaptation checks succeed, and the original adaptation timing sample is taken. Checkpoint identity uses consumed, evaluated input tokens, not an unconsumed bonus output. Every completed request can retain a recent head, whose additional copy latency must be measured.

Failed allocation, incomplete stages, denied budget, invalid metadata or failed publication do not advance the successful-capture schedule. Missing coverage remains explicit and sticky across in-memory parking. True cold replay or an appropriate rewind can repair history; a nonzero legacy restore cannot silently acquire trusted full-prefix coverage. Selected incoming images are detached before optional eviction can invalidate a cache index.

## Coverage guarantee and limits

The implementation records continuity of saved coverage metadata. A diagnostic value `coverage=complete` is not independent proof of GPU state equality or of a maximum opportunity gap.

If every snapshot succeeds, full state and identity are valid, and eligible safe capture opportunities have a proven maximum spacing S, matching-prefix reread is less than 16384 + S tokens. The changed/new suffix is extra. An exact 16384-token universal reread ceiling is not claimed. The observed opportunity spacing and GPU restoration behavior must be established in each supported path before advertising a bound.

See [MEMORY.md](MEMORY.md) for admission accounting, [BUILD.md](BUILD.md) for historical ABI rebuilding, and [VALIDATION.md](VALIDATION.md) for evidence and pending gates.
