# Guarded HC + grouped Q2_0 MMQ candidate

This is an opt-in prototype measured on the locked gfx906 exact stack, not a production promotion. It combines lossless-input-conversion HC with native fallback and the grouped Q2_0 J32 selection hint. It does not promise universal bitwise GEMM equivalence.

## Model results

Fresh native processes, fixed placement, INT8 KV, two gfx906 16 GiB GPUs with layer split 27/21, MTP window 16K, no prompt reuse. Six successful runs produced 1024 tokens each; all output IDs match within each pair.

| Prompt | Best PP | Combined PP | PP gain | Best TG | Combined TG |
|---|---:|---:|---:|---:|---:|
| Code 4K | 347.9591 | 361.6937 | 3.9472% | 55.9224 | 55.8757 |
| Code 64K | 598.3285 | 610.7980 | 2.0841% | 50.5048 | 50.5367 |
| Russian 64K | 598.1565 | 610.6956 | 2.0963% | 52.6982 | 52.7058 |

PP/TG are reported native prompt/generation tokens per second. These are combined measurements against the current best, not sums of isolated gains. The code64K pair was separated by a deliberate pause for a numerical falsifier; the finished candidate run was reused. The cancelled, zero-output baseline launch is excluded. These are single matched pairs, with prior independent HC/J32 screens providing supporting evidence.

## Correctness and limits

- Revised MMQ component harness: five geometries including imbalanced groups, empty experts, 31/32/33 and 63/64/65 boundaries, J48, and a single-expert control. Ten outputs per cap per GPU, 40 total, passed CPU tolerance/finite checks and untouched canary-row checks. All corresponding cap0/cap32 hashes match.
- The harness now pads destination IDs for upstream tile-tail reads. Existing production allocator padding already covers the GCN maximum; the smaller tile does not expand the requirement. Canary checks are not a general memory-safety proof.
- Prior strict HC tests cover 72 full-output native comparisons, including fast-route and fallback cases; see the strict-light report.
- An additional cancellation falsifier used W=0.25 and sparse X=(4,2^-22,-4) in four deliberate adjacent/boundary placements, with all scaled halves normal and losslessly represented. Both GPUs matched native bitwise; route counters confirmed three fast executions and one forced-native comparison. Both paths returned zero rather than the exact-real 2^-24 on these witnesses. This fails to falsify their equivalence, not a proof for arbitrary inputs or library algorithms.
- HC still invokes separate default BF16 and F16 library GEMMs. Exact operand conversion does not specify their reduction trees. Numerical equivalence remains empirical and limited to tested shapes, inputs and this pinned software/hardware configuration.
- The actual 200,000-token capacity pair passed: PP 574.0887 to 585.0057 tokens/s (+1.9016%), 256 output IDs equal, fixed expert residency preserved. TG 43.7465 to 43.6875 tokens/s. The partial final prompt chunk was exercised. Candidate API qualification passed: forced named tool call and result roundtrip, two synthetic images through the CPU vision process, text after image, 401 authentication and 404 UI checks, and A/title/A RAM prompt-cache restoration. The actual engine hash and opt-in environment were verified. Original live configuration and service were restored; no production promotion is claimed.

## Reproduction identity

Baseline binary: ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14.
Combined binary: 17b688afdca41976020cd2e2889d170c6fd29e39f84d1369a752b25b617f3228.
Source baseline b6731bf plus retained deployment patches; llama.cpp 3cf03257f219afbe7334045ff7c6a06ac68c627d. The new selector preserves p.max_rows as launch bound and changes only ncols_opt. Non-gfx906 builds, other formats and single-expert products are unchanged. Gating is a build macro, not a runtime architecture guard; this is not yet a generalized upstream patch.

Candidate additions to the exact-stack environment: STRATA_GFX906_HC_F16=1, STRATA_HC_F16_SCALE_PROBE=1, STRATA_HC_F16_EXACT_INPUT=1, STRATA_HC_F16_AUDIT=0, STRATA_GFX906_MMQ_OPT_CAP=32. No adaptive scale selection, approximate unguarded path, expert reordering or new persistent allocation is enabled. Diagnostic tracing was enabled for qualification. The existing live build was restored after each completed test window.
