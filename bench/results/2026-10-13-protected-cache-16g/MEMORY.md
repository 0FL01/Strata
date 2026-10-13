# The 16 GiB memory contract

The ceiling is exactly 17179869184 bytes. It covers accounted optional conversation-cache capacities plus outstanding pre-allocation reservations. The invariant is `owned + reserved <= limit`, with checked arithmetic and subtraction-based admission. Diagnostic `total` already includes `reserved`; never add it twice.

This is not a process RSS cap, a physical-RAM cap or a GPU VRAM cap. Model weights, base/live inference KV allocations, unrelated scratch and uninstrumented allocator overhead are outside this optional-cache ledger. Existing physical/container admission checks remain necessary.

## Charged ownership

The runtime charges active checkpoint banks, complete parked live/checkpoint/KV payloads and stage directories, retained/reusable KV, a detached selected incoming image, incomplete stage captures represented by their reservations, temporary split/copy/merge ownership, and a bounded identity/control reserve. Capacity rather than vector length is counted where relevant.

Snapshot admission includes old and new objects coexisting, deep-copied checkpoint banks, split identity copies and segmented-KV allocation peak estimates. A reservation must exist before allocation and outlive its payload, including cancellation, error and stack-unwinding paths. Failed final-capacity checks roll back unpublished work; they do not convert an already exceeded peak into a successful admission.

A precharged 32 MiB identity/control envelope is bounded by the gated configuration: old/new live and consumed token capacity at most 4 MiB, live image replacement capacity at most 16 MiB, and checkpoint/deque/map/policy/merge descriptors below 1 MiB. These are rounded capacity allowances, not an allocator/RSS-overhead promise. Large capture/split identity buffers are reserved separately. The request-length guard uses checked subtraction, so an `INT64_MAX` output request cannot overflow around the 256K envelope.

## Active bank and subordinate parking limits

At a 262144-token maximum context, 16 absolute anchors plus a root and two recent heads require at most 19 retained roles before deduplication. The current-model empirical estimate is about 2.118 GiB for those checkpoint payloads; temporary replacement, parked conversations, retained KV and other counted owners are additional. This estimate is not a universal formula for other models or stage layouts.

The parked-conversation settings remain 12288 MiB, four slots and an 8192 MiB minimum-free floor. The 12 GiB parked limit is subordinate to the global 16 GiB ledger, not an extra allowance. Measured per-stage geometry withholds enough future protected-bank growth from optional parking. Optional retained KV or whole parked lineages can be evicted; active protected anchors are not budget victims.

The ledger does not interpose a tracked allocator. Its guarantee depends on complete owner inventory and conservative pre-allocation peak estimates. CPU saturation/overflow/rollback tests establish ledger behavior but do not allocate 16 GiB or measure real process peaks. GPU diagnostics and physical memory telemetry remain distinct evidence.

## Measured v1 parking tradeoff

The protected bank is deep-copied into parked snapshots. In the first paired run, ordinary turns short01 and short04 copied respectively 356667760 and 475122120 additional snapshot bytes, with parking-time increases of 193.2 and 253.3 ms. This explains most of those requests' added prompt time. Eliminating unconditional recent-head copies does not remove this separate parking cost. All copies still require peak admission; immutable sharing is outside the present scope. See [the measured evidence](evidence/replay-v1/parking-overhead.json).
