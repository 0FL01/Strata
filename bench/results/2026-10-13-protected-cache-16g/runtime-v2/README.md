# v2: remove the unconditional request-end snapshot copy

Status: exact host rebuild **PASS**, including byte-identical baseline reproduction, eight host compilations, five CPU tests and owned cleanup. Candidate binary SHA256 is `2cbcd0eafb1385e4a345bb405e8c677e9fb77f3cbba46088d04c760fdd246ef2` (21669776 bytes). The strengthened 20-request GPU test gate passed, but deployment is **ON HOLD** because returning to the earlier ancestor rereads 47764 tokens instead of 6 and prompt time rises 962.7→82993.6ms. V2 has not been deployed. Upstream review identified a separate current-main pin-compatibility blocker; this historical patch is not directly upstream-applicable. This separate version must not inherit a GPU pass from v1, whose overall acceptance failed. The v1 patch and failed measurements remain preserved unchanged in the parent directory.

Candidate generate.cpp SHA256:

    f08929af779cc1d1fb6ac94d5a4adc1218ba091cf512ec69b146db887df88a5f

## Exact change

Apply the original historical-to-v1 `../runtime/protected-cache.patch`, then `request-head-elision.patch`. The second patch removes only the unconditional end-request `checkpoint_at(..., source="request_head")` block and replaces it with explanatory comments. The v2 helper/layout headers are byte-identical to `../runtime/include/`; no new header copy is needed. The sealed v2 build manifest and exact source/test hashes are recorded here.

Protected target scheduling, accounting, existing prompt captures, mandatory due decode captures, final commit wait, live-state publication and request-completion cleanup are unchanged. No GPU state format, kernel, chunk/window geometry, commit/draft ordering or immutable-sharing model was changed.

In v1, six extra request-head copies measured 514.553 ms and ordinary-turn decode time increased by 512.1 ms. Removing that recurring copy is a targeted optimization hypothesis. V2 now has one measured paired run: recurring request-head copies are absent and short-turn decode rates are essentially equal, but ancestor restoration regresses severely. See the parent validation record. Larger protected-bank deep copies during parking remain, so zero parking overhead is not promised.

## What the two recent slots mean

V2 retains up to two existing ordinary checkpoints with the highest use/capture stamps, excluding the protected anchors and root. In chat these are normally turn-boundary snapshots. It does not manufacture two snapshots or guarantee two completed-request endpoints. Prompts without turn markers can have no ordinary recent snapshots. Existing “two recent heads” wording should be read as this retention allowance.

This can preserve two useful prior turn boundaries instead of a turn boundary plus an independent copy of the current live endpoint. Some earlier-turn rewinds may therefore improve. Other off-grid rewinds lose v1's optional endpoint snapshot.

## Preserved behavior and explicit tradeoff

- Immediate continuation uses the coherent committed live state at the same evaluated endpoint.
- Existing parking on a switch/rewind captures the outgoing state as image.live, subject to the same byte/physical admission and whole-lineage eviction. Parking can fail admission and is not a universal replacement guarantee.
- Absolute 16K anchors are still captured in prefill, serial short verifier windows and due committed decode windows. The decode hook remains after the primary commit drain and before EOS/STOP exits.
- Consumed-token identity, prefix/image/control-vector validation, incompatible suffix pruning, final commit wait and coherent live publication are unchanged.
- Prompt cancellation never produced a terminal request-head snapshot in v1. Decode cancellation retains a coherent live endpoint and any due protected anchor.

V2 loses the separately owned checkpoint at each completed or decode-cancelled request's exact off-grid endpoint. If subsequent append-only work advances live without parking, a later branch to that old endpoint may need more replay from a prior turn/root/anchor. With no turn markers, anchors at 16384/32768 and completed endpoints 40000/40500, a later LCP 40200 could resume 40000 under v1 but 32768 under v2. Protected coverage remains unchanged; optional off-grid reuse does not.

The removed v1 endpoint call could also retry a due capture after an earlier admission miss. V2 removes that retry. The earlier failure already marked coverage degraded; a later v1 success did not clear its sticky hole. This does not weaken the healthy-path anchor schedule, and no stronger degraded-path guarantee is made.

## Evidence and next gates

The exact delta reconstructs the pinned v2 source, and all headers match v1 byte-for-byte. The new assertion-enabled recent-retention test covers ordinary turn snapshots, empty recent slots without turn markers, the lost off-grid example, earlier-turn preservation, live continuation, parked-live restoration, protected decode retention and cancellation-safe bank simulation. It complements the existing runtime contract; these host tests do not execute or restore GPU tensor state.

The stronger run reproduced the old root collapse and passed input/output parity, decode-anchor, cancellation, accounting and cleanup checks. Promotion remains blocked by the severe ancestor-return regression. Its cause must be established and the revised tradeoff/fix validated rather than treating the test gate as permission to deploy. Deployment and current-main integration remain separate actions.

The v2 host receipts and original-hash provenance are in [evidence/cpu-v2](../evidence/cpu-v2/). They verify source/ABI building only and do not establish GPU correctness or upstream merge readiness.

Current main has pin-aware parking semantics absent from this historical header. The historical global eviction loop cannot be transplanted unchanged without regressing those protections. See [UPSTREAM.md](../UPSTREAM.md).
