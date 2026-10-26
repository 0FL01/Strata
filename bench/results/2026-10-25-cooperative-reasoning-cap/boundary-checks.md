# Cooperative cap boundary checks
This test-only branch extends the experimental frontend branch without changing native or frontend implementation.
Actual Service/tokenizer CPU suite:15tests PASS, including clean wrap and genuine split closing-think tag at budgets1,2,3,4,5,8; prior UTF-8, EOS, cancellation/error, no-room and no-progress cases remain.
One fixed native process used the unchanged published executable. Fixed schedule: one8-token contiguous greedy reference, then caps1,2,3,4, each followed by one-token generation after appending the next known reference token. Nine calls,22emitted IDs, no retries or timing gate.
All capped outputs and continued outputs matched the reference. Fresh natural DONE counters were valid. Continuation reuse/read pairs were (8192,2),(8194,1),(8195,1),(8196,1).
Cap2 exercised accepted-T2 overflow (one draft offered and accepted) while preserving the delivered prefix. Cap1/2 directly reused live state. Cap3/4 restored previously parked longer prefixes: these are protocol/output checks, not isolated proof of each fresh cap-produced live state.
One appended known token is necessary because live admission requires at least one unconsumed prompt token. This models a nonempty append such as the existing18-token reasoning closure. Empty artificial continuations can legitimately reread; no zero-prefill guarantee.
EOS-at-cap was not exercised natively. Source/CPU coverage remains separate. No full-state bitexactness, performance or general task-quality claim.
The original publication candidate commit remains untouched. This is a separate local preservation branch; external publication is pending.
