# Protected absolute checkpoint coverage helper

`coverage.hpp` is a standalone C++17 host-policy helper. It performs no tensor allocation, synchronization, filesystem work, or global-budget mutation. It is intended only for an opt-in runtime path; legacy behavior is untouched until the runtime invokes it.

## Integration contract

- Namespace: `strata::program::coverage`.
- Add a distinct checkpoint metadata field `int64_t coverage_target = 0`. Do not reuse user pins or tail tags. Copy that field through every split/merge/copy/move path, including parked conversations.
- Keep a `State(step, maximum)` with each conversation lineage. Default step is 16384; maximum is 262144. Copy the complete State alongside the parked checkpoint bank, including sticky hole metadata. A disk schema without these fields must be rejected in strict mode or restored with explicitly untrusted coverage history.
- At an already-existing, coherent, fully committed endpoint L, `state.due(L)` is a cheap admission check. Preserve execution window/chunk geometry and label the snapshot with L, not a nominal target. Decode identity must use actually evaluated/consumed input tokens.
- Reserve the complete additional peak through the global memory controller before any payload allocation. The old checkpoint bank remains charged until replacement succeeds. Missing stage parts, denied admission, failed transfer, or failed final budget audit cannot publish an anchor.
- Only after successful exact-state capture or promotion, plus successful budget commit, call `state.saved(L)`. It returns the earliest covered absolute threshold; store that in `coverage_target` when the snapshot has no existing coverage tag. Deduplicate identical valid state; promotion should not make another payload copy. Updating an unpublished copy of State before transaction commit is safe if failure discards the copy.
- A capture may satisfy several crossed thresholds when opportunity spacing exceeds B. The metadata explicitly represents the range `[coverage_target, floor(L/B)*B]`; all those targets share one actual coherent snapshot at L. No state at an interior target is implied.
- On a required capture failure, call `state.failed(L, reason)`. This never advances `next_target`; a later save does not erase the historical hole. Stop advertising complete coverage. Reason labels include budget, incomplete_snapshot, transfer_failed, unsupported_mode, opportunity_gap, no_eligible_victim, and invalid_metadata.
- On branch/prune/restore, first discard every checkpoint whose complete identity is incompatible or lies beyond the valid prefix. Then `state.rebuild(lengths, targets, count, evaluated_through, trusted_history)` reconstructs the pending absolute target. Arrays need not be sorted. All retained lengths must be at/before the actual restored/evaluated endpoint. `trusted_history` means the original cold-origin history and its State were retained; it is not a claim that restoring at a nonzero point is equivalent to evaluating from zero.
- Rebuild retains existing hole status unless replay rewinds strictly before its affected threshold. True cold restart at zero clears untrusted history. Missing anchor intervals stay explicit holes; ordinary recent/root snapshots are not silently promoted. Explicit promotion can call saved at their real endpoint, while retaining any historical hole.
- `eviction_victim(lengths, stamps, targets, count, user_pins=nullptr, recent_count=2, tails=nullptr)` returns `std::optional<size_t>`. Minimum-length root, all anchors, all independent user pins, and two most-recent otherwise-unprotected snapshots survive. Used/capture stamp orders recents; length/index breaks ties. Eligible tails have priority over other eligible LRU victims. No victim is an ordinary admission failure: never erase index `count`, loop indefinitely, or invoke legacy pin fallback.
- Caller decides when it wants to discard ordinary extras. Repeatedly applying the selector until it returns no victim yields exactly root + coverage anchors + up to two ordinary recent heads + user pins, deduplicated at the checkpoint-object level. A fixed 19-slot limit accommodates 16 full-context anchors plus root and two recents; extra user pins require their own allowance and global byte admission.

`next_target == 0` means every in-context absolute target is represented. No global-memory controller is duplicated here; the separately owned `ConversationMemoryBudget` supplies admission. Untrusted or inconsistent metadata fails conservatively.

## Honest guarantee

A hole-free State records continuity of the policy's saved metadata. It does not prove numerical correctness, bound capture-opportunity spacing, or measure RAM/RSS. Before claiming a replay bound, the runtime must also establish complete exact-state validity, prefix identities, and the maximum eligible opportunity gap S across every supported path. Under those conditions, redundant matching-prefix reread is less than B+S; unmatched suffix work is additional. Unsupported pipeline capture must remain gated or explicitly degraded.

## Tests

Run `./run_tests.sh`; use `SANITIZE=1 ./run_tests.sh` for ASan+UBSan. `CXX` can override the compiler. Tests use assertions, so do not compile with NDEBUG.

Passed locally:

- Recorded request-22 creation trace retains 100786 and gives 33302 total prompt tokens read, with 9 anchors, root, and 2 ordinary recents.
- 1,048,580 exhaustive LCP checks at full 256K across opportunity maxima 64, 1024, 4096, and 32768.
- 1,600 random branch/refill cases and 8,457 short turns without request-relative timer resets.
- Root/anchor/recent2/user-pin isolation, promotion/deduplication, unsorted bank, and explicit no-victim saturation.
- Required budget/incomplete failures preserve the timer and old bank; sticky holes survive parking, and genuine rewind/replay can repair them.
- Legacy restore, missing intermediate anchor, cancel-before-commit versus eligible post-commit endpoint, multiple crossed targets, and int64 endpoints.
- Combined test against the actual global-budget helper: synthetic measured-model payload accounting at full 256K fits under 16 GiB with 13 GiB charged to other owners; one-byte-short peak admission rejects without protected loss.
- ASan and UBSan pass. LeakSanitizer itself is unavailable under the executor's ptrace environment; it was disabled explicitly after its environment-level fatal error.

These are host metadata/accounting tests. They do not create or restore actual GPU states, allocate the modeled multi-GiB payload, verify kernel/output parity, validate real pipeline ordering, or promise latency.
