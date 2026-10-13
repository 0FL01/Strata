# Checkpoint coverage investigation and bounded cache fix

Status: monitored opt-in historical-runtime deployment completed and passed its rollout checks at 2026-10-13 16:06:47 UTC (44 seconds). Paired GPU replay has exact output-ID parity and a documented history-dependent performance trade-off. The clean main-based source has host validation only, not a main-based GPU qualification.

## Selected implementation and attribution

This branch integrates the existing upstream PR #1959 unchanged for opt-in geometric spread, plus a separate all-ancestor supersession safety fix. The experimental higher-capacity coverage policy was rejected for deployment.

The spread implementation, flag, original host tests and `docs/DETAILS.md` addition are from **xrip**, original Git author `xrip <xrip@xrip.ru>`, commit `58cf9f4e6b9902b9a5334551110860c94e4f2202` in `xrip/Strata`, authored 2026-10-11. Source: https://github.com/Niko1221/Strata/pull/1959. That existing PR is not ours. This branch is an integration and reproduction record, not a competing upstream submission.

`--prompt-cache-spread` stays off by default and retains the existing checkpoint-count limit. The selected configuration is six checkpoints. There is no hard maximum replay-gap guarantee. No kernel, numerical-state format, or restore eligibility rule changes.

The additional cleanup fix is unconditional: every parked checkpoint must have an exact token/image match in the outgoing checkpoint chain or exact live state, with matching control-vector mode, before supersession may remove the entry. Memory remains constrained by the existing parked byte and slot limits. This can retain useful parked snapshots longer than the old deepest-only rule.

## Observed failure

A diagnostic run captured a valid intermediate checkpoint being evicted, followed by a request that could no longer use the recent checkpoints because its prompt diverged earlier.

- At 15:11:20 UTC, request 78 still had an eligible normal checkpoint at token 147,657.
- At 15:11:23.488605769 UTC, the same request evicted that checkpoint through the LRU path.
- Request 82 had 160,711 prompt tokens and shared 147,658 tokens with the 174,228-token live session. It could not use that whole live session.
- The retained normal checkpoints after the root were at 160,069, 162,526, 163,968, 165,478 and 169,818 tokens. All were beyond the actual common prefix. The root at 10,665 was eligible; resume selected it.
- Therefore 150,046 prompt tokens required reading. If the earlier valid checkpoint at 147,657 had survived and remained eligible, 13,054 would have required reading instead: 136,992 fewer tokens, by arithmetic. This is a counterfactual token-work estimate, not a measured speedup or a post-fix result.

No prompt text is needed to show this chain of events. The selected evidence file contains checkpoint metadata only.

## Scope and trade-offs

The proposed work concerns checkpoint coverage retention and safe cleanup of parked snapshots. Exact prefix, image, control-vector and state compatibility checks must remain authoritative. An arbitrary K/V prefix is not a substitute for a saved recurrent-state checkpoint.

The selected same-capacity spread policy avoids adding a second checkpoint pool. The rejected experimental policy reserved periodic points in addition to recent turns and used more memory for the captured trace.
Cleanup must not call an old parked copy redundant merely because its deepest checkpoint remains in the outgoing chain: older resumable checkpoints may provide unique coverage. Conversely, preserving every historical copy is not a promise of unbounded retention; ordinary byte, slot and physical-memory gates still apply.

## Upstream overlap and attribution

Checked through GitHub on 2026-10-13 around 15:27 UTC. Latest main observed: [a0116b2782a5b82622358c04a06496485d12b2d6](https://github.com/Niko1221/Strata/commit/a0116b2782a5b82622358c04a06496485d12b2d6).

- [PR #1959](https://github.com/Niko1221/Strata/pull/1959), open and unmerged, already addresses the same LRU-collapse failure with opt-in `--prompt-cache-spread`. At head `58cf9f4e6b9902b9a5334551110860c94e4f2202`, its policy keeps the same checkpoint count. Among eligible interior points, it removes the smallest `(next - previous) / (newest - previous)` ratio. It preserves the root/newest and explicit pins where possible, prioritizes a tail victim, and falls back to the existing policy. This is direct prior art; do not create a competing novelty claim or silently reuse its flag for another algorithm.
- [PR #2265](https://github.com/Niko1221/Strata/pull/2265), open and unmerged, adds opt-in `--conversation-cache-park-gain` to reduce repeated full snapshot copies. Head `58ca3f2929b4e357ce2867b8981a246fdb881ac5`, based on a0116b2. Its new accessor deliberately mirrors the existing deepest-checkpoint-only supersession rule. Coverage-safe supersession is a distinct concern; combining them requires updating the accessor and cleanup contract together.
- [PR #1537](https://github.com/Niko1221/Strata/pull/1537), open and unmerged, saves a checkpoint when continuing the live session after a long generated reply. It adds a checkpoint at a different event; it does not solve retention of older checkpoints once created.
- Existing main already includes root-pinned LRU, explicit shared-prefix pins, tail handling, conversation supersession, checkpoint-copy changes and watchdog progress. Those are prerequisites and must not be described as new work in this patch.

## Same-incident policy comparison

A host replay of the captured request 73–81 checkpoint lengths produced:

- Existing LRU: six retained checkpoints; resume at 10,665.
- Upstream PR #1959 spread: six retained checkpoints; resume at 147,657.
- Proposed coverage policy: eleven retained checkpoints; resume at 147,657.

At the request-82 common-prefix boundary of 147,658, both alternatives avoid the same 136,992 tokens of rereading. The spread policy achieves this result with five fewer retained checkpoints. This incident alone does not justify claiming the higher-capacity policy is better. A distinct bounded-spacing guarantee, if desired, requires its own tests and explicit memory trade-off.

This replay uses creation order (equivalent to the relevant LRU ordering), not full GPU/server execution. It does not simulate additional hypothetical absolute-cadence anchors. The raw output is in `incident_comparison.txt`.

## Publication layout

Use a new bounded branch based on verified upstream a0116b2 for the clean source patch, host tests, and this evidence. Branch name: `fix/checkpoint-retention-20261013` (remote publication is owned separately).

Preserve the historical runtime integration separately. An incremental patch against the exact deployed historical source is the deployment artifact; it is not interchangeable with a patch against current main. Record each artifact's base SHA or content hash. Keep the prior integration files and rollback binary/config unchanged. Do not overwrite or rebase existing branches or PRs.

The existing gfx906 PRs #1187, #1320, #1535 and #1743 are separate work. No change to them is part of this publication preparation. A new upstream PR should not be opened until the relationship to #1959 is resolved and review validation is adequate.

## Validation matrix

| Check | Current status | Required interpretation |
|---|---|---|
| Captured LRU eviction and root-only resume | Observed in diagnostics | Proves the pre-fix failure chain |
| Upstream #1959 host policy test | Passed locally, C++17 | Tests public reference policy only, not proposed fix |
| Same-incident trace policy comparison | Host replay completed | LRU: 6 points / resume 10,665; #1959: 6 / 147,657; proposed coverage: 11 / 147,657 |
| Retention tests | Passed | Original #1959 policy tests and added short-turn/tail/pruning host model |
| Coverage-safe supersession tests | Passed | Main-based conversation_cache_test: 4,227 checks; includes 8 new assertions |
| Host sanitizer run | ASan + UBSan passed, leak detection disabled | 4,227 checks; LeakSanitizer unsupported under this executor ptrace |
| Historical HIP candidate and paired GPU replay | Executed | 16 requests per arm; exact output IDs match across arms; mixed performance below |
| CUDA / SYCL builds | Not run here | Required before claiming all-backend qualification |
| Paired GPU replay output parity | Passed for this replay | All 16 request output-ID sequences match; broader numerical/workload guarantees are not claimed |
| Deployment receipt / immediate health | Passed | Candidate binary hash and enabled spread verified; healthy loaded model, context/image/auth settings preserved |
| Sustained live reuse / crash / memory observation | Ongoing, no completion claim | Immediate health alone does not prove long-run behavior |

## Rollback and final provenance

The sanitized `deployment.json` records the verified baseline, candidate and live binary hashes, configuration backup, settings and rollout timestamps. Binary identity was checked after restart. Publication must still name its remotely verified branch commit and CI status; this local report does not claim either exists.

## Reproduce host tests

Run from the repository root (C++20 is required by the core header):

```
c++ -std=c++17 -O2 -Wall -Wextra -Werror -Iinclude src/program/conv_cache_test.cpp -o /tmp/conv_cache_test
/tmp/conv_cache_test
c++ -std=c++20 -O2 -Wall -Wextra -Werror -Iinclude src/core/conversation_cache_test.cpp -o /tmp/conversation_cache_test
/tmp/conversation_cache_test
c++ -std=c++20 -O2 -Wall -Wextra -Werror -Iinclude bench/results/2026-10-13-checkpoint-retention/spread_regression_test.cpp -o /tmp/spread_regression_test
/tmp/spread_regression_test
c++ -std=c++20 -O1 -g -fsanitize=address,undefined -Iinclude src/core/conversation_cache_test.cpp -o /tmp/conversation_cache_test_san
ASAN_OPTIONS=detect_leaks=0 /tmp/conversation_cache_test_san
```

The first attempted core build with C++17 was rejected because the existing core header requires C++20. It was rerun with C++20 successfully. An initial sanitizer run could not complete LeakSanitizer under ptrace; disabling leak detection allowed the ASan/UBSan run to pass. No leak-check pass is claimed.

## Historical deployment artifact

`historical-deployment.patch` is an incremental patch for the previously instrumented historical runtime source, not for this branch's a0116b2 source tree. SHA-256: `1824e156b5c36fb44287b1bae85502263bdc759aa8900d2936c2335f91f23286`.

Exact input SHA-256 values:

- `src/program/generate.cpp`: `12c332b42add6b1cdba7038ea5825642c098c7296586fc2b0310760581b98823`
- `include/strata/program/conv_cache.hpp`: `349e1a1aa6a4e0e609d09dcbfba5c8d9e75fa81d64c2748b1b00e3216b429278`
- `include/strata/core/conversation_cache.hpp`: `a6c2e017497d38663d391b290662e74b37aa99147e1ca7e12c02f2204f81168b`

Verify all three before applying it. The historical generator already contains diagnostics and runtime-specific integration; this patch preserves that base. Its added diagnostics report spread mode and checkpoint bytes. Those diagnostics are not injected into the clean main generator.

## Paired GPU replay: history-dependent trade-off

The paired historical-runtime replay completed 16 requests per arm. All corresponding output-ID sequences matched, and the active checkpoint count remained capped at six. This is evidence for output parity on this replay; it is not a blanket correctness or speedup claim.

| History-dependent request | Baseline reuse / read | Candidate reuse / read | Baseline prompt seconds | Candidate prompt seconds |
|---|---:|---:|---:|---:|
| rewrite65560 | 16,384 / 49,435 | 65,536 / 283 | 78.1315 | 3.1061 |
| later rewrite33024 | 32,768 / 515 | 16,384 / 16,899 | 3.6297 | 29.8804 |

The later rewrite materially regresses despite the earlier win. These are prompt-phase timings within a stateful paired replay, not independent cold-start comparisons. Final parked-cache state also differs: baseline two parked entries and zero evictions; candidate four entries and six evictions. Same active checkpoint count therefore does not imply identical total cache behavior or equal parked-memory pressure.

The actual checkpoint logs identify the history effect. Baseline request 11 performed the expensive reread and created a new checkpoint at 32,768 (`used=25`). Request 12 parked it. Request 13 then selected that exact checkpoint from the parked conversation. The candidate avoided request 11's reread by resuming at 65,536, so it did not recreate the 32,768 checkpoint at that time. Its later rewrite therefore resumed at 16,384 and reread more. This is the expected trade-off of geometric retention and different preceding work, rather than an observed output correctness failure. The increased parked-slot pressure remains a separate observation.

Across all 16 requests, baseline read 118,344 tokens in 211,824.3 ms of prompt time; candidate read 85,576 in 165,410.2 ms. These totals describe this one paired, stateful replay only. They do not establish a broad speedup, a worst-case replay bound, or an isolated estimate of either component's benefit.

The rollout is monitored and opt-in, with slower older edits and parked-cache pressure explicitly disclosed. Deployment passed its rollout checks at 16:06:47 UTC. Source is unchanged. This GPU run qualifies the historical-runtime candidate only; the clean a0116b2-based publication tree has not been built or run on a GPU.
These results were reported by the deployment coordinator from the paired run. Filtered checkpoint metadata and the per-request comparison are included in `gpu-replay-attribution.json`. Raw user prompts and raw runtime logs are not included.

## CPU archive / inline-definition consistency

The baseline and candidate recompiles of the `conversation_state`, `conversation_file`, and `conversation_snapshot` objects were byte-identical to their corresponding pinned-archive objects. All six comparison gates passed. This closes the scoped archive-consistency check for those three objects and both header configurations. It does not erase the observed runtime-policy regression or qualify untested backends.

## Deployment and rollback

The bounded opt-in admission was approved after the exact checkpoint-history attribution and paired aggregate results were reviewed. Rollout completed at 2026-10-13 16:06:47 UTC in about 44 seconds.

- Live/candidate binary SHA-256: `74aa76d48a4783991e60b7e25601125dc5dc2bfeeaa351a71b350c122476b662`.
- Previous binary SHA-256: `85f8d642f42a52fa0e6402838e1755ea5ec3923155bd92fb3c2ac42415c02f56`.
- Configuration changes: executable selection and `--prompt-cache-spread` enabled.
- Verified health: status `ok`, model loaded, maximum context 262,144, images enabled, API-key authentication enabled. The receipt records only the authentication boolean, never a key.
- Checkpoint diagnostics remain enabled (`1`); the unsafe peer flag remains absent.
- Configuration backup, relative to the deployment repository: `configs/shefowl-hybrid-200k-c183-winner-live-20261013.json.before-cache-retention-fix-20261013`.

For a full rollback, restore that backed-up configuration, including its previous executable selection and arguments, and restart the same service through the deployment procedure. Verify the running executable matches the previous binary hash above, then recheck loaded/health, context, images and key-auth settings. Merely removing `--prompt-cache-spread` is not a full rollback: the candidate's stricter superseded-copy cleanup remains compiled in. Keep the previous binary and configuration backup until monitored operation is accepted. No credential, private host route or absolute server-home path is included here.
