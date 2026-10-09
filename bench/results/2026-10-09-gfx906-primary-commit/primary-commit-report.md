# Primary only commit overlap qualification

Status: 2026-10-09. The default-off scheduling optimization passed the bounded 64K performance screen, exact-output checks at 4K, 64K and 200K, and temporary API qualification. The immutable release `gfx906-qualified-20261009-commit` is preserved. Production was not promoted. This report and patch archive is separate from an implementation branch; no upstream PR for this scheduling change has been created.

## Main result

Four matched runs in A1–B1–B2–A2 order, each with 65,536 prompt tokens and 1,024 generated tokens, measured **+1.212502% token-generation throughput (TG)**. Mean control throughput was **51.620202 tokens/s**, versus **52.246098 tokens/s** with overlap enabled. Matched pair gains were **+1.278774%** and **+1.146300%**. All 1,024 output IDs were identical across all four runs; acceptance and cache counters also matched.

This passes the specified engineering gate: mean TG gain at least 1%, both matched pairs positive, and exact output IDs. Two pairs do not establish statistical confidence or performance across other workloads. Prompt-processing throughput (PP) changed **+0.038093%**, a noise-level observation rather than evidence of prefill acceleration.

| Arm | Overlap | Prompt ms | Decode ms | PP tokens/s | TG tokens/s |
|---|---|---:|---:|---:|---:|
| A1 | off | 104916.2 | 19847.5 | 624.650912 | 51.593400 |
| B1 | on | 104861.9 | 19596.9 | 624.974371 | 52.253162 |
| B2 | on | 104911.1 | 19602.2 | 624.681278 | 52.239034 |
| A2 | off | 104936.7 | 19826.9 | 624.528883 | 51.647005 |

The gain is the ratio of mean B throughput to mean A throughput, minus one. Pair comparisons are B1/A1 and B2/A2. TG is actual generated tokens divided by native decode time. PP is reported full prompt count divided by native prompt time; the last prompt token executes in the first decode window. Model load and request wall time are retained separately in the accompanying JSON. The headline is a decode-throughput gain, not an end-to-end request speedup.

## Comparison scope and configuration

The control is the already-qualified user fork stack, identified by binary SHA-256 `050dd8dcbe7d3e9cfaeae870d45df872a1aecded6fff1e1d4611d52f1194c4f4`. It already includes the prior selected optimizations, including empty-PCIe dispatch elision. The new result measures the incremental effect of primary commit overlap on that stack.

An earlier direct comparison of that pre-overlap stack against the user's stable `ce` control is a separate experiment. Neither that stable control nor this overlap control represents stock upstream. Do not add isolated optimization percentages, infer a newly measured overall-stack gain from them, or attribute an overall stack result to this patch. No fresh post-overlap full-stack-versus-stable comparison is reported here.

The measured setup uses two distinct gfx906 devices, ordinary serial serving with MTP, int8 KV, context capacity 204,800, resident KV 32,768, effective PCIe share zero, 19,078 expert slots including 9,900 primary, speculative setting 6, MTP maximum 4, lookup setting 3 and 15 pool workers. All arms used temperature 0, top-p 1, top-k 1 and seed 12345, with no prompt reuse. Each 64K arm recorded 648 accepted / 872 offered speculative tokens and 582,049 cache hits / 600,000 lookups. Diagnostic overlap trace is kept separate from performance measurement.

## Scheduling change and safety contract

The optimization defers only the primary GPU's commit completion. After the unchanged verify stages finish and the accepted-token count is known, the host enqueues primary commit on its existing stream, executes the secondary GPU's synchronous commit, and runs the existing MTP draft on the secondary GPU. An explicit device-aware drain completes primary commit immediately after drafting, before policy observation, cancellation exit or the next decode iteration.

The commit kernels, arithmetic, graph identities, mapped-input fence, per-stage stream order and verify-stage run/handoff synchronization remain unchanged. Secondary commit stays synchronous. The primary's graph operates on its own layer-sliced session and verifier buffers; it does not write the secondary residual used by MTP, the cross-device handoff, or MTP's separately owned cache. Host PLE-history advancement remains before drafting.

Ownership is tracked independently of whether completion-event recording succeeds. Event-record or event-wait failure attempts a direct stream drain, retains ownership unless completion is confirmed, and preserves the original error. A scoped cleanup guard covers exceptional host work after enqueue. Undrained ownership blocks the next run's capture/staging and commit's mapped-parameter rewrite. Failure to fence a failed device is not treated as successful completion or safe session reuse.

The drain is mandatory even when drafting is skipped, ends early, fails, or reaches EOS or the output-length limit. Existing prompt, final-request, persistence, parking and batch-transition boundaries are retained. T=1 self-commit launches no new commit graph and requires no new completion event.

## Activation and fallback behavior

`STRATA_PRIMARY_COMMIT_OVERLAP` is enabled by **presence**. Setting it to `0` still opts in; unset it to disable. `STRATA_PRIMARY_COMMIT_TRACE` also uses presence, so `=0` still enables tracing. Keep trace unset for performance measurement. Presence of `STRATA_COMMIT_SYNC`, including a value of `0`, overrides the feature and forces the synchronous baseline.

Compile eligibility accepts either `STRATA_USE_HIP` or `STRATA_HIP_GFX906`. Runtime eligibility requires exactly two stages on distinct gfx906 devices, serial serving with MTP, and no batch, pipeline or shared-device split. Missing opt-in, unsupported backend or architecture, failed property queries, absent MTP, non-serving or prompt calls, and excluded execution modes retain baseline scheduling.

An earlier USE_HIP-only activation guard silently excluded the actual gfx906 compatibility build. That revision is superseded and must not be used. The final corrected patch is SHA-256 `3c87611bd665e3cd4a3525d1536977e2c7a7b8ce22730fc8fa4c8ea36f532d90`.

## Qualification evidence

### Source and host checks

Independent source review checked buffer ownership, unchanged commit capture/staging arithmetic, primary-only call propagation, error cleanup and drain ordering. The source checks and 16 abstract fault-state models passed. The fault models are not GPU fault injection and do not demonstrate recovery from a failed device.

The actual eligibility block was compiled in 63 mocked host cases: 21 each for the qualified gfx906 compatibility definitions, native HIP definitions, and neither backend macro. The tests used the real architecture helper and mocked runtime inputs. Eligible device pairs activated only on supported routes, and excluded cases failed closed. Replacing the corrected guard with the old USE_HIP-only guard made the negative control fail, detecting the original activation regression.

### Runtime smoke checks

Flag-off, flag-on and force-sync requests produced identical outputs. Enabled diagnostics confirmed actual primary enqueue and drain; the short-length T=1 case produced no enqueue. The JSON preserves both requests from each smoke arm, including 32-token and 1-token outputs, raw completion fields and request wall times. These diagnostic timings are not performance evidence.

### Short and long context checks

| Qualification | Control TG | Candidate TG | Result |
|---|---:|---:|---|
| 4,096 prompt / 1,024 output tokens | 56.807150 | 57.735679 | +1.634529% TG; exact 1,024 IDs |
| 200,000 prompt / 256 output tokens | Archived reference only | 44.600080 | Capacity and exact 256-ID parity passed |

The 4K test was one candidate-first/control pair. Native decode times were 18,025.9 ms control and 17,736.0 ms candidate. PP was 368.972444 versus 369.735156 tokens/s, a **+0.206712%** noise-level change. This single pair corroborates the bounded result but provides no statistical-confidence claim.

The 200K candidate completed in 334,982.4 ms native prompt time and 5,739.9 ms native decode time, with PP 597.046293 tokens/s. All 256 IDs match the archived empty-PCIe qualification reference. Both ID arrays and their numeric receipts are preserved for independent checking. **There was no fresh 200K performance control and no 200K speedup is claimed.** The archived timing is provenance, not a matched speed comparison.

### API and cancellation checks

The temporary candidate passed tools, vision, parking and cancellation checks. The receipt identifies the running candidate binary as SHA-256 `8900243a832bde09818b7fc0fa922ad7d430891b3d378e10a370ba7a9fa0a1bf`.

The cancellation check disconnected an HTTP stream after 12 chunks; the engine recorded 14 output tokens and a disconnect finish. A subsequent request returned `42` in the same engine process. This supports the tested early-disconnect/reuse path; it does not establish all cancellation timings or GPU fault recovery.

API validation finished at 07:54:08 UTC on 2026-10-09. The original configuration and compose files were restored byte-for-byte, all five RND source files were restored, and the original service was healthy. The immutable candidate release was retained without production promotion.

## Artifacts and independent checking

- Corrected scheduling patch SHA-256: `3c87611bd665e3cd4a3525d1536977e2c7a7b8ce22730fc8fa4c8ea36f532d90`.
- Qualified candidate binary SHA-256: `8900243a832bde09818b7fc0fa922ad7d430891b3d378e10a370ba7a9fa0a1bf`.
- Prototype source base: `f152172332693c933b8a3104ce193d8a4315c2b4`, with the qualified fork-stack changes; the bare commit alone does not recreate the measured stack.
- Required empty-PCIe patch SHA-256: `7e41dbdb97df1f451ee7c3b5c70c248995d37c36db9650ab2b49a240004b2174`.
- Immutable release label: `gfx906-qualified-20261009-commit`.
- Sanitized receipt: `primary-commit-results.json`, containing model, qualification, smoke, API, archived-reference and recheck sections.

The JSON retains all output IDs and numerical timings from the relevant model, qualification and smoke receipts, plus the archived 200K reference. Native PP/TG arithmetic, ABBA order and gain, both 64K pair gains, 4K parity, 200K archived-reference parity and smoke-request parity were rechecked offline. API fields are explicitly whitelisted; credentials, environment mappings, private hostnames and absolute controller paths are excluded.

This report supports a narrowly qualified, opt-in fork-stack change. It establishes no upstream-baseline performance, other-device or other-KV benefit, batching/pipeline benefit, universal token parity or model-quality improvement. Report preparation used read-only controller receipts and local artifact generation; it performed no GPU access, build, push, deployment or publication.

## Receipt and host recheck

Run `python3 bench/check_gfx906_primary_commit_results.py bench/results/2026-10-09-gfx906-primary-commit/primary-commit-results.json --selftest` from the archive checkout. The validator checks preserved arithmetic and token IDs and rejects six deliberately corrupted receipts. See `bench/GFX906_QUALIFIED_RESULTS.md` for the separate temporary-worktree host guard test. These commands do not rerun GPU/API qualification.
