# Upstream review and remaining port work

Reviewed 2026-10-13, 18:19–18:24 UTC. **Future upstream PR work remains open.** This directory is a historical-runtime preservation/results bundle, not a current-main implementation or an upstream-ready patch.

The verified upstream is [Niko1221/Strata](https://api.github.com/repos/0FL01/Strata), whose exact reviewed main is [a0116b2782a5b82622358c04a06496485d12b2d6](https://github.com/Niko1221/Strata/commit/a0116b2782a5b82622358c04a06496485d12b2d6). The existing [preservation commit 236a6aa](https://github.com/0FL01/Strata/commit/236a6aac2da7c2df00b1510f8fe46270917e2334) was one commit ahead and zero behind that main. Its source delta combines strict all-ancestor cleanup with the already-proposed geometric spread policy from [PR #1959](https://github.com/Niko1221/Strata/pull/1959); that combination must not be presented as wholly new work.

## Actual applicability check

A read-only `git apply --check` of the historical v2 delta against fetched main returned exit 1. Both `src/program/generate.cpp` and `include/strata/core/conversation_cache.hpp` failed to apply. See [the exact check output](evidence/upstream/historical-apply-check.txt). No cherry-pick or candidate/other-PR merge was attempted.

The failure reflects semantic differences, not just shifted lines. Current-main generate.cpp had 13585 lines versus 11797 in the historical candidate. Current main includes:

- [Shared-prefix pin metadata](https://github.com/Niko1221/Strata/blob/a0116b2782a5b82622358c04a06496485d12b2d6/include/strata/core/conversation_cache.hpp#L23-L43), split propagation, and [pin-aware eviction](https://github.com/Niko1221/Strata/blob/a0116b2782a5b82622358c04a06496485d12b2d6/include/strata/core/conversation_cache.hpp#L264-L304).
- Minimum-length parking admission, longest-parked-token tracking and complete invalid-state cache clearing.
- [Physical host/cgroup admission](https://github.com/Niko1221/Strata/blob/a0116b2782a5b82622358c04a06496485d12b2d6/src/program/generate.cpp#L7883-L8058) and [shared-prefix request/pin-sibling handling](https://github.com/Niko1221/Strata/blob/a0116b2782a5b82622358c04a06496485d12b2d6/src/program/generate.cpp#L10440-L10449).

The historical candidate lacks `ConversationCheckpoint::pinned` and its global eviction removes `entries_.front()` without a pin check. Direct transplantation would regress current-main protections. A real port must preserve pins independently of coverage anchors, use pin-aware eligible victims and refuse optional admission when all potential victims are pinned. Held/selected images and retained KV must remain charged through every transfer/refusal.

Current main still uses [deepest-checkpoint domination in drop_superseded](https://github.com/Niko1221/Strata/blob/a0116b2782a5b82622358c04a06496485d12b2d6/include/strata/core/conversation_cache.hpp#L306-L334), so the all-ancestor correctness repair remains a distinct small change. Its port must retain the newer cache methods and pin handling.

## Relevant open PR interactions

These are inspected semantic/source-region overlaps. Except for the historical-to-main dry run above, they are not measured merge conflicts or successful composition tests.

- [#1959, geometric retention](https://github.com/Niko1221/Strata/pull/1959): spreads a fixed-size legacy bank rather than protecting all absolute safe-opportunity anchors. The preserved branch already contains this work. A novel protected-policy PR should link/credit it and avoid duplicating its separate feature; default-off protected mode can leave legacy LRU unchanged.
- [#2265, low-growth re-parking](https://github.com/Niko1221/Strata/pull/2265): its parked-prefix accessor mirrors the old deepest-checkpoint dominance predicate. After the ancestor fix, use a shared dominance predicate or explicitly redefine the growth gate. Skipping parking must also preserve required coverage/provenance. This is complementary performance work, not part of the first minimal port.
- [#2253](https://github.com/Niko1221/Strata/pull/2253) and [#2082](https://github.com/Niko1221/Strata/pull/2082), admission/retained KV: both introduce evictable-byte logic and overlap with each other. Physical RAM/commit headroom and the optional-cache ledger are different gates; both must pass. Only unpinned, actually reclaimable images count, and retained KV handback must be re-accounted once on refusal paths.
- [#1559, stale pins](https://github.com/Niko1221/Strata/pull/1559): pin retirement crosses active, slot and parked state. Replacing a user pin must not unprotect a coverage anchor; a coverage role must not keep stale user pins permanently alive.
- [#1503, retained-KV identity](https://github.com/Niko1221/Strata/pull/1503): adds token identity and invalidation around reused KV. If composed later, identity capacities and lifetime enter the global ledger. The historical batch-disabled profile does not fix or qualify the general cross-conversation issue.
- [#1511, snapshot reuse/chain moves](https://github.com/Niko1221/Strata/pull/1511): relevant to measured protected-bank parking copies, but moves/reuse change ownership, transient peaks, reservations and rollback. GitHub reported this PR itself dirty/unmergeable against its base at review time; that is not a composition result with this candidate. Defer this optimization until the port's correctness is established.
- [#1537, live-continuation checkpoints](https://github.com/Niko1221/Strata/pull/1537): related to v2's optional off-grid endpoint tradeoff, but not equivalent to an unconditional terminal copy or a due protected decode anchor. Any combined ordinary snapshot requires separate admission and retention.
- [#2247, BF16 stored-state codec](https://github.com/Niko1221/Strata/pull/2247): changes the numerical contract and introduces variable sizes/conversion scratch. Do not bundle lossy state into this exact-state fix.
- [#2094, immutable branch contexts](https://github.com/Niko1221/Strata/pull/2094): broad experimental sharing/branch API with allocation-identity accounting. Shared ownership cannot be composed by simply summing independent capacities. It is not an already-available cure for parking cost.
- [#1752, gfx906/HIP file-tier behavior](https://github.com/Niko1221/Strata/pull/1752): touches a separate expert_source path and addresses a different host-pressure/KFD mechanism. Keep it and other GPU tuning/build preservation separate.

Disk/session, prefix-file, shared-borrowing and remote-checkpoint proposals were also screened. They introduce additional provenance/ownership paths and are not implicit dependencies. Protected disk/session restore can remain explicitly unsupported in the first port. Open PR status alone does not show that a feature is absent from main: for example, the minimum-token behavior discussed in #1597 is already present in fetched main.

## Scope of the review

All 518 open PR records were enumerated and their titles/bodies screened. The review inspected 27 relevant changed-file lists and 41 non-null source patches, then refreshed 12 high-priority PR heads/statuses. No equivalent combined absolute-16K protected-anchor/global-capacity policy was found in that bounded inspection. This does not exclude unpublished or differently-described related work.

Some very large per-file patch responses were unavailable for #1779/#1887/#2098; their metadata/file lists were inspected, with correspondingly limited region claims. No “all conflicts checked” or “clean merge” claim is made. GitHub's clean flag on another PR is not proof that this future PR composes with it.

Exact reviewed base/head SHAs and observed statuses are in [reviewed-heads.json](evidence/upstream/reviewed-heads.json). Re-fetch main and relevant PR heads before any publication or readiness assertion.

## Proposed two-PR split, still to implement

1. **Correctness-only ancestor preservation.** Port the all-ancestor `drop_superseded` predicate onto current main, retaining pins and every newer method. Add focused tests for unique older ancestors, fully dominated banks, same-position token mismatch, image/steering mismatch and empty banks. Coordinate dominance semantics with #2265. This fix preserves available states; it does not manufacture missing anchors or independently solve sparse-bank coverage.
2. **Default-off protected coverage and global accounting.** Stack on the small repair or land afterward. Port capture/reservations to current main; retain root, independent user pins, actual safe-opportunity anchors and two existing recent ordinary checkpoints. Expose a validated configurable global cache budget rather than a universal hardcoded 16 GiB policy, while retaining 16 GiB for the measured profile. Preserve physical admission, poisoning/cache-clear behavior, min-token handling and exact consumed-state identity. Keep unsupported paths gated and make failures/degraded provenance explicit.

Before either proposal is called ready, build/test its actual current-main commit. The larger change also needs same-sequence off/on parity, a fixture reproducing real root collapse, due-decode restoration, continuation/EOS/STOP/cancel/error cleanup, budget and context edges, pin/no-eligible-victim tests, and separate reporting of remaining parking-copy costs. Historical MI50 results do not certify current-main CUDA/SYCL/HIP behavior.

This report completes a bounded investigation. The requested future port/PR work remains outstanding; no upstream PR was opened as part of this review.
