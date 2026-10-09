# Complete c183 stack versus optimized stable ce

## Direct result

Fresh-process **A1/B1/B2/A2**, 65536 prompt tokens and 1024 output IDs per arm:

| Native throughput | Stable ce, mean A | Complete c183, mean B | Direct gain |
|---|---:|---:|---:|
| PP, tokens/s | 598.318773666 | 647.068551491 | **+8.147793%** |
| TG, tokens/s | 50.532092076 | 53.821369818 | **+6.509285%** |

Both pairs improved:

- PP: B1/A1 **+8.021570%**; B2/A2 **+8.274111%**
- TG: B1/A1 **+6.507937%**; B2/A2 **+6.510633%**

This is a direct comparison of the complete c183 stack with **already optimized stable ce**, not stock upstream. Percentages were measured directly, not added from isolated optimization results. This experiment is separate from the earlier ff34-versus-ce comparison.

## Raw measurements

| Arm | Prompt ms | Decode ms | PP | TG |
|---|---:|---:|---:|---:|
| A1 | 109492.5 | 20264.2 | 598.543279220 | 50.532466123 |
| B1 | 101361.7 | 19026.0 | 646.555849004 | 53.821086934 |
| B2 | 101201.2 | 19025.8 | 647.581253977 | 53.821652703 |
| A2 | 109574.7 | 20264.5 | 598.094268111 | 50.531718029 |

PP = 65536 × 1000 / native prompt_ms; TG = 1024 × 1000 / native decode_ms. Each mean averages the two corresponding per-arm rates. Gain = 100 × (candidate_mean / stable_mean − 1). Load and request-wall times are retained separately; they are not included in these native rates. Means and pair gains were independently recalculated.

## Quality, topology and policy accounting

All four complete 1024-ID arrays exactly match the historical default reference. Engine topology and every available recorded counter also match across the four arms:

- Accepted/offered drafts: 648 / 872
- Cache hits/lookups: 582049 / 600000
- Prompt reused/read: 0 / 65536
- RAM blobs, file blobs, file MB and offloaded experts: all 0
- Suffix windows/accepted/offered: 5 / 9 / 16

Both paired counter-delta records contain zero for every available numeric field. Five optional lookup-chain fields were not emitted by the normal 16-field DONE protocol; those values and deltas remain **null/unavailable**, not zero.

**Observed aggregate counter equality is not proof of constant work.** The default DraftPolicy remains timing-trained, and detailed per-window work was not instrumented. This is a practical end-to-end comparison including policy behavior, not isolated selector attribution.

Requests retained the original default native args and greedy seed 12345, fixed slots 19078/9900, layer split 27, INT8 KV, context capacity 204800 and resident KV 32768. Requested spec 4 with default suffix drafting reports verifier geometry 6, MTP maximum 4 and lookup 3. The candidate retains the qualified ff34 optimizations and enables scalar FIT17; stable ce uses its verified original environment. New profiling/trace switches remained off.

## Provenance and operational scope

- Stable binary SHA256: `ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14`
- Candidate binary SHA256: `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`
- Input fixture SHA256: `63ce3d4042027a00b2193feab143f1d9443b5c31a863a962ec9543ccb54d9695`
- Original summary SHA256: `91883277001d9b6c31d92a14563125e36fdffeee3fc8901b4e31b591968707c2`
- Run window: 2026-10-09 16:35:07.744882–16:45:44.437340 UTC

The receipt preserves all four output arrays, native and suffix counters, explicit pair deltas, release flags, source/build/qualification hashes, sanitized manifests and hashes of all 13 original result/manifest/thermal/summary files. Each standalone result was checked against its summary entry before consolidation.

Each arm has 27 thermal samples. Recorded modes/caps remained high / 190 W; observed maxima across the study were 61 / 81 / 62°C for temp1/temp2/temp3. These are discrete observations, not continuous thermal proof.

The API was untouched, owned containers were cleaned up, and the runner did not modify stable configuration or promote the candidate. Private paths, configuration contents and raw logs are excluded. One completed ABBA is not a broad-workload study or a confidence interval; no further runs were selected to obtain a favorable result.

## Offline validation

    python3 check_direct_c183_vs_ce_results.py direct-c183-vs-ce-results.json --selftest

Validation passed: arithmetic, full IDs, topology, release profiles, nullable counters, pair deltas, provenance and scope checks. **14 intentional corruption cases were rejected.** The validator checks receipt consistency without rerunning or independently authenticating hardware measurements. The report was prepared from the completed receipts and validated offline.


Run the command from this report directory. [Numeric receipt](direct-c183-vs-ce-results.json) · [Validator](check_direct_c183_vs_ce_results.py).
