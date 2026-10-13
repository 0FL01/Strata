# Global conversation-cache budget

Header: `include/strata/core/conversation_memory_budget.hpp`

CPU test: `tests/test_conversation_memory_budget.cpp`

## Scope and invariant

The default ceiling is 17,179,869,184 bytes = 16 GiB = 16,777,216 KiB. It is an all-inclusive **accounted conversation-cache capacity and reservation ceiling**, not a process RSS or physical-RAM ceiling. Model/expert RAM, live inference KV, unrelated scratch, allocator implementation overhead, GPU memory, and other processes are not automatically instrumented by this helper. A physical host/container admission check remains a separate requirement.

The ledger always satisfies `owned + reserved <= limit`, using checked arithmetic and subtraction-based admission. A failed reconciliation or final-capacity audit leaves the last valid ledger intact, marks it breached, and rejects new reservations until rollback and a successful reconciliation. Never report a breached snapshot as a current inventory of actual memory.

The helper does not allocate payloads and does not interpose a tracked allocator. It only enforces a valid caller's pre-allocation reservations. Final `commit` checks net owned growth; it cannot detect a larger earlier transient hidden by simultaneous frees. Allocation peaks must be bounded independently before allocation.

## Exact API

Namespace: `strata::core`

`ConversationMemoryInventory` has mutually exclusive `size_t` fields:

- `active`: complete active checkpoint bank, including its outer vector capacity.
- `parked`: complete parked images, excluding separately charged retained KV.
- `retained`: retained/reused KV, including detached reuse locals during parking.
- `selected`: a selected image removed from the cache but still alive.
- `inflight`: materialized stage parts not covered by any outstanding ticket.
- `temporary`: separately owned split identity copies, rollback states, and other temporary buffers not covered by a ticket.
- `metadata`: additional directory/control capacity and an explicit, documented allocator/scratch margin if the runtime chooses one.

`bytes(size_t& out)` returns false on overflow; `bytes()` saturates to `SIZE_MAX`.

`ConversationMemoryBudget budget(limit_bytes)` owns a mutex-protected ledger and must outlive every ticket.

- `bool reconcile(inventory)`: audit current ownership at a serialized boundary. This does not authorize an earlier allocation. A successful call also clears a prior breach after rollback.
- `Reservation reserve(additional_peak)`: reserve before allocation. Invalid token means skip capture and record the policy's explicit budget coverage gap. Zero-byte reservations are valid tokens.
- `bool Reservation::commit(new_inventory)`: atomically exchange that ticket for the full new inventory. Net owned growth must not exceed ticket size, and other tickets remain charged. Success consumes the ticket; failure preserves it for rollback.
- `void Reservation::reset()`: release ticket after covered uncommitted allocations have been destroyed.
- `bool Reservation::shrink(new_bytes)`: release excess only after its temporary allocation is gone or a tighter remaining peak has been established. Cannot grow a ticket.
- `Snapshot snapshot()`: inventory, owned, reserved, total, limit, high_water, outstanding, breached, last_failure.
- `size_t available()`: additional unreserved capacity, or zero when breached.
- `size_t parked_headroom(subordinate_cap)`: current total allowance for parked plus retained owners after nonparked owners and outstanding reservations. It is not additional free space and is not an admission token.

`conversation_memory_add(a, b, out)` and `conversation_memory_multiply(a, b, out)` fail without changing `out` on overflow. Check their boolean results; do not turn overflowing estimates into zero.

## Runtime contract

1. Serialize ownership mutation and inventory sampling with the runtime's own lock. The helper's mutex protects only its ledger, not external vectors. Concurrent capture tickets are supported, but a pending capture's materialized bytes must remain represented by its ticket until that capture commits. Do not count them again in another operation's inventory.
2. Reconcile all existing owners before first admission and after releases, moves, evictions, cancellation, or invalidation. A move between parked, selected, retained, active, and inflight must conserve bytes; do not remove charge merely because an object left `ConversationCache`.
3. Reserve all stages and all temporary overlap before stage zero allocates. Keep old checkpoint owners charged through replacement. Count pending checkpoint positions explicitly. Capture denial must preserve existing protected checkpoints and mark the missing anchor's coverage gap.
4. Reserve checkpoint-split identity/directory copies **before** `conversation_checkpoints_split`, and preserve that charge until merge has destroyed redundant storage. Count old and new directory overlap during merge. Count active `checks.capacity()`, partial-state maps/containers, checkpoint `stage_parts.capacity()`, every nested parked image, and `stage_images.capacity() * sizeof(SavedConversation)` omitted by the historical `SavedConversation::bytes()` implementation.
5. Retained KV is already owned, including after `take_reuse()`. Snapshot additional allocation is its audited peak minus the already charged owned buffers, never the full final snapshot plus those same buffers. Use `ConversationBuffer::allocation_peak()` for appending/growing reuse; a final byte estimate alone can miss directory overlap or geometric spare capacity.
6. Keep selected incoming state charged while parking outgoing state. Optional parked eviction must re-audit actual freed capacity. If the 12 GiB parked cap remains, apply it under the current global allowance; it cannot authorize overcommit against active/selected/inflight memory. Reserved future active-bank growth also needs to reduce optional parked space without being counted twice when capture uses that planned allowance.
7. On success, atomically commit a full, coherent captured anchor before publication. If `commit` rejects, destroy unpublished capture, release its ticket, reconcile remaining owners, and mark the anchor budget gap. A failed multipart capture must not expose a partially complete checkpoint.
8. Arrange C++ lifetime order carefully: create the reservation before the payload, or declare the token member before payload members, so payload destruction happens before ticket destruction during stack unwinding. Tickets are move-only and move assignment first releases the destination's previous reservation.
9. Batch-slot copies and disk SAVE/LOAD must either join the same inventory/pre-admission contract or be explicitly rejected while the opt-in is enabled. No global-bound claim should silently omit enabled duplicate owners.
10. A safety margin is not a substitute for bounding actual capacities. This helper has no invented automatic margin; runtime diagnostics must identify any chosen margin, what it covers, and what remains unmeasured. Strict allocated-byte/RSS enforcement requires allocator instrumentation beyond this ledger.

## CPU validation

Commands run with GCC 14.2.0:

```
g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic -pthread -Iinclude tests/test_conversation_memory_budget.cpp -o test_budget
./test_budget
g++ -std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic -pthread -fsanitize=address,undefined -fno-omit-frame-pointer -Iinclude tests/test_conversation_memory_budget.cpp -o test_budget_asan
ASAN_OPTIONS=detect_leaks=0 ./test_budget_asan
g++ -std=c++20 -O2 -DNDEBUG -Wall -Wextra -Werror -pedantic -pthread -Iinclude tests/test_conversation_memory_budget.cpp -o test_budget_release
./test_budget_release
```

All three runs passed 8 CPU test groups: exact-budget and zero cases; checked arithmetic/overflow; move/shrink/exception safety; ownership transfer conservation; old+new replacement and complete-stage reservation; underestimated-capture refusal and fail-closed rollback; concurrent reservations/atomic commit; dynamic subordinate parked cap and invalid inventory audit.

LeakSanitizer with `detect_leaks=1` could not run because this execution environment uses ptrace, which LeakSanitizer rejects. AddressSanitizer and UndefinedBehaviorSanitizer passed with leak checking disabled. No GPU/backend build, server mutation, deployment, peak RSS measurement, or runtime integration test was performed by this worker.
