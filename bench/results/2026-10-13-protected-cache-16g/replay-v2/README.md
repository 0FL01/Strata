# v2 regression fixture: require real root fallback before comparison

This separate 20-request fixture reproduces the same retention-failure mechanism as the historical report using deterministic synthetic traffic. It is not byte-exact user traffic. V1's weaker fixture and failed acceptance remain preserved in `../replay/` and `../evidence/replay-v1/`.

The run completed and the defined test gate passed: hardware baseline root fallback was reproduced; candidate compaction read 123414→33302 with prompt time195967.1→60340.3ms; paired inputs/outputs, decode-anchor restoration, cancellation and accounting matched. **Deployment remains on hold.** The ancestor-return case regressed from 6 to 47764 read tokens and from 962.7 to 82993.6ms prompt time. The test contract allows optional ancestor eviction, so its `passed=true` must not be interpreted as deployment acceptance. See [the full result](../evidence/replay-v2/summary.json).

## Why this fixture is stronger

The CPU proof uses the exact historical `spread_victim` and `ConversationCache` policies, including strict all-ancestor supersession and the four-slot FIFO. It reproduces all 23 recorded evictions. An exhaustive search of increasing recorded turn boundaries found four growth requests sufficient to collapse the active checkpoint bank to root 10674: 133472,135692,136089,147644. Three additional parking requests displace older parked banks that might still contain 84402/100786. Neither parked-cache slots nor its 12 GiB cap is disabled/reduced.

Each deliberate tail rewrite retains the first 16 actual emitted IDs, then edits the next token to ensure a real rewind while preserving existing turn checkpoints. This handles accepted speculative windows that may have consumed beyond the 32 emitted outputs. The exact CPU selection code then proves both active and best parked reuse at 10674 for LCP 117131.

The host proof uses token-only snapshots and assumes normal successful snapshot admission; it does not allocate model tensors or real GPU-sized snapshots. The launcher therefore checks actual baseline reuse 10674/read 123414 immediately after compaction and stops before candidate launch if the runtime does not reproduce it. A model-only proof cannot excuse a different hardware result.

## Request sequence

1. Initial prompt 128561 with root 10674 and turn 128556; 32 outputs.
2. Four recorded growth boundaries 133472,135692,136089,147644; 32 outputs each.
3. Three bounded park-churn requests at 147932,148220,148508; 32 outputs each.
4. Compaction to prompt 134088 at exact LCP 117131, requiring baseline root fallback and candidate gain.
5. Rewind to prompt 130900 at LCP 130894, then generate 512 outputs, ensuring target 131072 is crossed during decode.
6. Rewrite at LCP 131100 and require an actually saved/restored decode anchor at 131072..131100.
7. Decode cancellation after at least 8 observed IDs, identical-input recovery, and pre-compaction ancestor restoration.
8. Six ordinary live-growing turns after the correctness gates, each prompt 288 tokens longer and 32 native outputs, for separately reported overhead.

That is 20 requests per arm. All 19 noncancel inputs and complete output sequences must match; cancellation compares the common emitted prefix. Optional parked eviction/admission refusal can occur without invalidating the test if parity, protected coverage and accounting remain valid. There is no required request-head snapshot count: v2's removed unconditional copies are judged by semantics and actual timing.

## Public reproduction and limits

The public code includes the numeric historical creation/eviction trace, exact policy headers, CPU selection proof and protocol tests. It omits the original prompt seed; its SHA256 is recorded in `source-pins.json`. The parent public CPU runner supplies a generated synthetic seed, so it checks fixture/protocol behavior without revealing original token data. A measured GPU reproduction requires the authorized operator's exact pinned seed.

The launcher's `/srv/...` paths are sanitized examples. As with v1, verify actual host paths/devices/configuration, matching passed build receipt, candidate/baseline hashes, GPU exclusion, temperatures and explicit GPU-window admission before use. It runs arms sequentially, does not deploy and restores the previously running baseline service after owned cleanup. A start request alone is not model/API health evidence.

Preserve the measured geometry and memory gates: PP 4096, spec 6, split 27, context 262144, no batch/pipeline, parked cap 12288 MiB/four slots, free-memory floor 8192 MiB and global optional-cache limit 17179869184 bytes. Both arms retain the baseline spread flag; the protected flag differs only on the candidate. The test-only EOS override is not a deployment configuration change.

Captured-event `bytes` means complete bank bytes, and `ms` excludes some earlier multipart save work. Do not sum them as copied bytes or total capture cost. Use end-to-end PP/TTFT/wall and the six ordinary-turn breakdown. One paired run is not statistical proof, image/semantic validation, universal GPU-state equivalence or an RSS guarantee.
