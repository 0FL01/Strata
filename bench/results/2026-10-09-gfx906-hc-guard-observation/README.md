# HC guard observations: attribution and lifetime investigation only

Date: 2026-10-09 UTC. Decision: **ATTRIBUTION_AND_LIFETIME_INVESTIGATION_ONLY**.

Two single-request diagnostics establish a repeated exactness-rejecting weight population, but do not establish removable guard time or a safe negative-weight-cache lifetime. The conditional 64K host-wall screen is **13,579.974339 ms**, above the **1,003.739604 ms** screening threshold. This deliberately generous quantity contains required queued predecessor work and double-counts overlapping stages. It is **not a model bound, saving or gain estimate**. No cache patch, model qualification or promotion follows from this result.

The existing c183 control remains [646.4538059 PP / 53.8075120 TG tokens/s at 64K/1,024](../2026-10-09-gfx906-c183-profile/README.md). Neither diagnostic measures a candidate throughput improvement.

## Provenance recovery and observer scope

A stale capture-verifier host object had survived an earlier binary restore. Recovery repaired only a scratch link closure to reproduce the exact c183 baseline before these diagnostics; original production source, objects and executable were unchanged. The baseline SHA-256 is `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.

The counts and cost observers were host-only scratch builds. The independently checked cost build retained all **55 embedded device payloads byte-for-byte**. It introduced no GPU event calls, launches, copies or synchronizations. The wall bracket uses a host monotonic clock immediately before the existing stats reset through the existing final synchronization. Logging is retained at context destruction, after the observed work, rather than introducing per-observation output inside the bracket.

Each probe used one fresh process, one 12,288-token prompt and one requested output, with no automatic retry. The HC chunks were 4096/4096/4095 at offsets 0/4096/8192. Counts ran 23:06:00–23:06:55 UTC; cost ran 23:31:44–23:32:39 UTC. Both native and wrapper exits were zero. Independent raw audits reconciled complete lifetime/readers, artifact hashes, admission bindings and cleanup. The API remained stopped; the high performance mode and 190 W caps were unchanged.

## Counts and negative evidence

Both probes observed **192 logical weights and 576 attempts: 203 taken and 373 exactness rejections**. There were no range or early rejections. Guard classes were 203 both-good, **313 X-only-bad**, 28 W-only-bad and 32 both-bad. Thus most rejection observations would not be addressed by a negative weight cache.

Exactly **20 distinct W-bad weights** failed in all three chunks, giving 60 W-bad observations and **40 repeated observations** after their first hit. Primary device 0 had 11 such weights / 22 repeats; peer device 1 had 9 / 18. Every nonzero W mask was 4, the exactness bit. All 192 identities had one first observation and two same-visible-generation repeats, with no changed-generation repeat, pointer change, address epoch or W-mask change.

W-bad zero-based layers were:

- Attention down: 0, 7, 18, 28, 32, 43, 44
- FFN down: 1, 3, 9, 16
- FFN up: 7, 20, 24, 41, 42
- Attention up: 11, 35, 44, 46

The numeric archive retains all 192 logical identities and all 576 integer-nanosecond guard observations. Stable visible bindings and masks are not a proof against in-place mutation, and do not validate reuse across future sessions or prefixes. Exact safe weight lifetime remains unproven.

## Guard-wall screen and its limits

For W-bad observations, primary first-hit/full-repeat/tail-repeat sums were **543.746409 / 580.603746 / 582.151970 ms**. Peer sums were **324.970928 / 323.646415 / 338.320115 ms**. First hits are reported separately and excluded from the repeat screen.

The conditional 64K scenario uses, per stage, `14 × measured full-repeat sum + measured tail-repeat sum`: 165 primary and 135 peer repeats. This gives **8,710.604414 ms primary** and **4,869.369925 ms peer**, summing to **13,579.974339 ms**. It assumes unchanged shapes, W-bad population, eligibility, visible and content lifetimes, and per-observation costs. It is not an observed 64K run.

Host wall includes work already queued ahead of the guard. Source ordering establishes that required predecessor GPU work remains on the same stream if the guard is skipped; it cannot be counted as removable guard service time. Down projections contribute **12,504.149463 ms, about 92.08%**, of this conditional screen. This queue-position pattern does not apportion the observed wall between predecessors and the guard itself. Any host-submission lookahead benefit remains unmeasured.

The primary and peer stages overlap, so their sum intentionally double-counts overlap. Do not add it to GPU phase timings or treat it as critical-path savings. Crossing the threshold permits only attribution and lifetime investigation. First reconcile existing component measurements and source dependencies; a new measurement or implementation requires a separately justified plan. The earlier [fixed-scale component screen](../2026-10-09-gfx906-hc-fixed-scale/README.md) remains parked.

## Independent audit and publication scope

Counts audit: **PASS_INDEPENDENT_RAW_COUNTS_LIFECYCLE_RECONCILIATION**. Cost build audit: **PASS_ACTUAL_COST_BUILD_AND_COMPLETE_DEVICE_EQUALITY**. Actual cost audit: **PASS_ACTUAL_COST_PROBE_RAW_AUDIT**. All 576 saved observation rows, stage sums, populations and gate arithmetic were independently checked against the raw receipts. No audit GPU rerun was performed.

[Machine-readable metrics](metrics.json) retain sanitized numbers, all per-observation nanoseconds, source/build/admission bindings and audit hashes. Private receipts, model/capture payloads, token IDs, pointers, credentials, host paths and binaries are excluded from this report-only update. No production code, engine settings or existing implementation PR is changed.
