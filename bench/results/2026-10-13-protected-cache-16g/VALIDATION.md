# Validation record

## Passed CPU/build gates

Both original CPU receipts report `passed=true`. The builder reproduced the baseline executable byte-for-byte and produced candidate `7b00d34c…` after eight host compilations, four assertion-enabled CPU test executables and zero GPU-kernel compilations. Archive/ODR closure, donor immutability, rollback preservation and owned-container cleanup passed. See the sanitized receipts and exact-original hashes in `evidence/cpu/`.

CPU coverage includes:

- 1,048,580 exhaustive LCP checks, 1,600 branch/refill cases and 8,457 short turns through a full 256K context.
- Root/coverage/recent2/user-pin separation, safe promotion/deduplication and no-victim saturation.
- Sticky missed-capture provenance, cancellation, missing-stage nonpublication, branch repair and overflow-safe scheduling.
- Eight ledger test groups covering concurrent reservations, ownership transfer, old/new overlap, overflow, failed reconciliation/rollback and subordinate parking headroom.
- Checkpoint split/merge, image/role mismatch rejection, parked metadata copy/move and selected-image detachment before eviction.
- Source ordering checks for unchanged deferred-commit/draft/chunk calls, reservation before GPU copy, publication before schedule advance and consumed-token decode identity.

ASan/UBSan host helper and runtime checks passed during preparation with leak detection disabled. LeakSanitizer itself was unavailable under the executor's ptrace restrictions; no leak-check pass is claimed. CPU tests neither allocate the modeled multi-GiB memory nor validate real GPU tensor state.

## GPU v1 result: completed, acceptance failed

The paired v1 run completed all 13 requests in each arm. Both native protocols passed, every input hash matched, all 12 noncancel output sequences matched exactly, and the common cancellation output prefix matched. Both arms emitted nine cancellation tokens and subsequently completed the 32-token recovery request. Decode restoration and ancestor restoration produced matching outputs.

Overall acceptance is **false**. On compaction at LCP 117131, both arms restored 100786 and read 16604 tokens, so read reduction was zero. The initial fixture did not reproduce the historical fallback to 10674 and cannot establish repair of that original regression. This is an insufficient regression fixture, not evidence that protected anchors can never help. A separate exact-history stress fixture remains required.

The candidate saved a decode anchor at 131072 and restored it for the LCP 131100 rewrite. That request read 287 tokens instead of 462, a reduction of 175. Its wall time still increased from 5.207 s to 5.608 s. Successful token reuse must not be presented as a latency win.

The candidate's 46 protected diagnostics and 13 request-completion meters passed accounting/coverage checks. Highest sampled accounted ownership was 13994425392 bytes; the ledger's reported high-water mark was 14121793268 bytes (13.152 GiB), below 17179869184 bytes. These are optional-cache ledger values, not process RSS. The fixture did not intentionally saturate the 16 GiB ceiling.

### Ordinary-short-turn overhead

For the six ordinary short turns, both arms read 1606 prompt tokens and emitted 192 outputs:

- Wall: 20.456 s baseline, 21.532 s candidate, **+5.26%**.
- Prompt processing: 17170.7 ms to 17643.1 ms, **+2.75%**.
- Decode: 3145.2 ms to 3657.3 ms, **+16.28%**.
- Mean first-token latency: 2917.34 ms to 3011.06 ms, **+3.21%**; median: +0.98%.

The six new request-head copies report 514.553 ms in total (about 85.76 ms each), closely matching the 512.1 ms decode-time increase. This strongly implicates those copies as an overhead source, but one sequential pair is not a controlled causal proof or a statistically qualified regression estimate. The entire run's wall time rose from 287.140 s to 292.714 s (+1.94%). Preserve the short-turn breakdown rather than hiding it inside the long-prefill aggregate.

The prompt-time increase also has a separate parking component. On short01, parking rose from 1419.1 ms to 1612.3 ms (+193.2 ms out of +203.0 ms prompt time); the copied bank grew from six to nine checkpoints and the snapshot grew by 356667760 bytes. On short04, parking rose from 1426.2 ms to 1679.5 ms (+253.3 ms out of +255.7 ms prompt time); the bank grew from six to ten checkpoints and the snapshot grew by 475122120 bytes. These measured deltas support the protected-bank deep-copy explanation. Exact selected diagnostic lines and source-log hashes are in [parking-overhead.json](evidence/replay-v1/parking-overhead.json).

Removing unconditional request-head captures addresses the separate decode-overhead component. It does not remove the larger protected-bank parking copies or promise zero overhead. The bounded tradeoff is more retained reusable state versus additional admitted host memory and copy work. Immutable sharing would require a separate, broader refactor and is outside this change's scope.

The wrapper passed owned cleanup and verified unchanged binary/configuration inputs. It requested restart of the previously running baseline API; the operator separately verified that API/model recovery was healthy. The candidate was **not deployed**. Work on a separately versioned copy-elision candidate and a stronger fixture is ongoing; v1 evidence must remain attributed to binary 7b00d34c….

Machine-readable original-result derivatives, per-case metrics, source hashes and field-level redaction notes are in [evidence/replay-v1/](evidence/replay-v1/). The raw private prompt/output arrays and server logs are omitted. The verified source archive SHA256 is 9667ce07f7d6886c77bf499e77890abadbb19f15def943eb510a764cf5f1c75a.

## Initial 13-request fixture and acceptance contract

The paired replay runs the exact baseline and protected candidate sequentially in the same pinned environment and production geometry. Its 13 requests per arm cover:

1. A 117173-token initial prompt with the old 117170 checkpoint boundary.
2. Six ordinary short turns to expose recency churn and new end-of-request capture overhead.
3. Compaction with exact LCP 117131.
4. Extension to 130900 prompt tokens and 512 outputs to cross target 131072 during decode.
5. Rewrite at exact LCP 131100, requiring an actual decode-created checkpoint at 131072..131100 and restoration from that range.
6. Decode cancellation after at least eight observed outputs, then a repeat request to verify recovery.
7. Restoration of the original pre-compaction ancestor.

The run compares identical input hashes before interpreting output parity. All 12 noncancel requests must match their full output IDs; cancellation compares the common emitted prefix. Absent/malformed accounting, coverage gaps, raw accounting-breach errors, incomplete requests, native errors, failed decode restoration, absent compaction improvement or parity drift fail acceptance. Every candidate request must emit a complete cache meter with `total=owned+reserved`, `total<=limit`, `high_water<=limit` and limit 17179869184.

The seed and raw prompt/output material are private and omitted from this bundle. Only its original SHA256 is published. Protocol tests can use a synthetic seed but cannot reproduce the measured model output without the original inputs. The runtime command overrides EOS only for the bounded test so requested decode lengths are reached; this is not a deployment EOS change.

## Timing interpretation and remaining limits

Record per-case actual prompt tokens read, prefill and generation timings, measured first-token latency, wall time, capture events/counts and request-head overhead. The captured-event millisecond field measures checkpoint_at/assembly and does not include all earlier multipart on_stage_chunk save time; it is a partial diagnostic, not total snapshot cost. Report the six ordinary short turns separately. Use end-to-end prompt/TTFT/wall timings to judge actual capture overhead. Capture work is already inside those observed request times; do not add the partial captured-event milliseconds to them or sum that field as total snapshot cost. The capture diagnostic `bytes` field is bank bytes, not bytes copied, and must not be summed as copy traffic. Baseline capture time is unavailable, not zero.

A single paired run is diagnostic evidence and does not establish a statistically qualified throughput claim, semantic model quality, universal full-state equivalence, or a 16 GiB RSS ceiling. The fixture does not intentionally saturate 16 GiB. Real image input, broad model geometries, batch/pipeline and disk persistence remain outside validation.

The v1 candidate was not deployed; current-main integration has not been performed. Test-window baseline recovery was independently checked, as described above. Original-regression acceptance, copy-overhead remediation and repeat validation remain open.

## Separate v2 host build

V2 source `f08929af…` rebuilt successfully into binary `2cbcd0ea…`. Its own receipts prove exact baseline reproduction, eight host compilations, five assertion-enabled CPU tests, unchanged qualified GPU objects/donor inputs and successful owned cleanup. No GPU inference ran during that build. The stronger regression replay remains pending; v1 text-parity results cannot be transferred to v2. Upstream review has identified a current-main pin-compatibility blocker documented in UPSTREAM.md. A future current-main port will need separate validation.

## Stronger v2 replay: test passed, deployment held

The 20-request v2 pair completed. The original root-collapse prerequisite was reproduced on hardware; every paired input hash matched and all comparable output IDs matched. Decode-anchor reuse, cancellation/recovery, protected accounting and owned cleanup passed. The original wrapper correctly records `passed=true` under its test contract. **Deployment acceptance is false and v2 was not deployed.** That test allows optional ancestor eviction and therefore does not guard against every unacceptable latency tradeoff.

### Compaction improvement

For the 134088-token prompt at LCP 117131:

- Baseline reused 10674 and read 123414; candidate reused 100786 and read 33302.
- Prompt processing improved 195967.1→60340.3ms.
- End-to-end request wall time improved 196.667→61.040s.

This is direct evidence of the protected policy avoiding the original sparse-bank/root-fallback failure for this fixture. It is still a single paired result, not a universal/statistical speedup claim.

### Blocking ancestor-return regression

Returning to the pre-compaction ancestor:

- Reuse fell 148544→100786.
- Prompt tokens read rose 6→47764.
- Prompt processing rose 962.7→82993.6ms.
- End-to-end wall time rose 1.541→83.571s.

These are different metrics: 0.9627→82.9936s describes prompt processing, not total wall time. Exact output parity still held, but the large latency regression is an explicit deployment blocker. The earlier lineage's eviction/selection is under investigation, including why it was lost while reported global high-water remained below 16 GiB. No root-cause conclusion or stronger retention guarantee is asserted yet.

### Whole-run and short-turn context

Whole-run wall time fell 526.743→484.575s (about 8.01%), but that aggregate must not hide the ancestor regression. The six ordinary short turns rose 17.7801→18.6160s (+4.70%). Nearly the entire difference came from short01: wall 2.874→3.720s, prompt +847.6ms and 36 extra tokens read. Short02–06 were near-identical in this pair. Aggregate short-turn decode throughput was 62.174→62.202 tokens/s, with no request-head captures. This supports elimination of v1's recurring head-copy cost while leaving state-transition/parking costs visible.

The highest sampled optional-cache accounting was 12886842056 bytes and reported high-water was 13015229960 bytes (12.121 GiB), below the 16 GiB ledger limit. This is not process RSS, and unused global headroom alone does not explain the lineage-retention decision.

The wrapper verified unchanged source binary/configuration inputs, cleaned owned jobs and requested restart of the baseline API. Its restart flag alone is not an independent health check. The production candidate was not changed by the replay. Current-main porting and the future upstream PR remain separate outstanding work.

Full per-case comparison, public result derivatives, meter samples and original-file hashes are in [evidence/replay-v2](evidence/replay-v2/). Raw prompt/output token arrays and full server logs are omitted. The verified source archive SHA256 is `dff5ce3b766270ebde7214d75c997373fd640d2595c911aeb9bbd1f00b18695c`.
