# Scalar FIT17: two separate model studies

## Results

Both completed studies passed their predeclared decode gate: mean TG ≥ 1%, both TG pairs positive, PP ≥ −1%, with the required exact-output checks.

| Study | Control TG | FIT17 TG | TG gain | PP gain |
|---|---:|---:|---:|---:|
| Suffix-disabled fixed-policy | 53.192595973 | 53.944301427 | **+1.413177%** | −0.001826% |
| Default adaptive policy | 53.147344202 | 53.838212538 | **+1.299911%** | +0.084680% |

Units: tokens/s. These are **different workloads**, one completed A1/B1/B2/A2 sequence each. Do not pool their gains or add them to earlier optimization results.

Every arm used the same c183 binary, changing only FIT17=0/1/1/0 within its study. Both retained the qualified ff34 stack, including primary-commit, empty-PCIe, HC/J32, dequant and QSA reduce12/query-swizzle. Native requests used 65536 prompt tokens, 1024 generated IDs, greedy seed 12345, fixed slots 19078/9900, context 204800, resident KV 32768 and layer split 27. All eight complete output arrays match the historical default IDs. Model traces/profiling stayed off.

## 1. Suffix-disabled fixed-policy study

Requested spec 6, MTP maximum 4, suffix draft 0; INFO reports `spec=6`, `mtp_max=4`, `lookup=0`. Actual MTP windows remain probability-gated 1–4, not universally T4.

- PP: 646.689194321 → 646.677388535 tokens/s
- TG paired gains: **+1.333551% / +1.492828%**
- All recorded counters matched across four arms: accepted 647, offered 868, cache hits 580670, lookups 598560; no suffix draft summary was emitted
- This result applies to the suffix-disabled profile, not the default profile

## 2. Default adaptive-policy study

Original requested spec 4 with default suffix 3 auto-expands to verifier geometry 6; INFO reports `spec=6`, `mtp_max=4`, `lookup=3`. This was predeclared as a **practical end-to-end test including timing-trained DraftPolicy response**, not constant-work selector attribution.

- PP: 646.288107072 → 646.835385420 tokens/s
- TG paired gains: **+1.404777% / +1.195194%**
- Pair B1−A1: all available recorded counter deltas 0
- Pair B2−A2: offered +2, cache hits +939, lookups +960; suffix windows +1, suffix accepted +2, suffix offered +4. Accepted output-draft count stayed 648; output IDs/topology stayed exact

Counter equality was deliberately not this study's gate. The second pair includes a measurable policy/work change, which must remain part of its interpretation. Five optional lookup-chain counters were not emitted by the default native protocol: they and their deltas remain **null/unavailable**, never invented zero. `INFO lookup=3` describes suffix drafting; it does not enable the optional lookup-chain protocol tail.

## Earlier outcomes remain distinct

| Stage | Preserved outcome |
|---|---|
| Original component 30% screen | **FAIL retained**: GPU 0 scalar latency reduction 26.927284%, below 30% |
| Additional scalar budget check | GPU 1 reduction 26.360542%; 12-layer proxy saved 0.625125111 ms, observed-extrema proxy 0.622845504 ms versus 0.51258 ms budget. This justified a bounded model test; it was not a measured model gain or rigorous bound |
| Initial historical-counter gate | **FAIL retained**, FIT17 off, A1 only. Exact 1024 IDs and accepted 648, but offered 873 vs 872, hits 582512 vs 582049, lookups 600480 vs 600000. No candidate arm or complete ABBA was reached |
| First adaptive parser attempt | **Infrastructure failure retained**, A1 only. Native process exited 0; the harness incorrectly required 21 DONE tokens instead of default 16. Native rate/ID results were not persisted, so none are reconstructed or claimed |
| Adaptive-v2 repair | Same binary/settings/gate; base 16 accepted, optional chain tail handled explicitly, private raw DONE/IDs saved before validation. A fresh output preserved the failed attempt; this was not a performance-selected retry |

The broader diagnostic sweep covered 30 processes, 834 windows and 4836 rows with parity passing, including exploratory variants. Hist2 was discarded; the production patch is scalar FIT17 only. Scalar scratch/spills were reduced but not eliminated; no spill-free claim is made.

## Additional correctness, not another benchmark

The separate correctness-only candidate checks passed:

- 4K prompt: all 1024 IDs exactly match qualified ff34
- 200K prompt: all 256 IDs exactly match qualified ff34

FIT17 host topology tracing was enabled for these checks only. Fallback ownership is explicitly **inferred** from verified step construction, source guards, known request geometry and production ISA checks: 4K decode remains on the guarded `reference256` path; 200K exceeds the 17408-block scalar capacity and uses guarded `reg66`. The host trace is not a device-branch counter. These unpaired runs establish no new throughput gain.

## Provenance, arithmetic and limits

Candidate binary SHA256: `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.

Qualified base SHA256: `ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9`.

The receipt binds the production patch, all seven compiled source hashes, object/build hashes, fixtures, individual result/manifest/thermal source hashes and full numeric output arrays. Build/restoration and production ISA/resource prechecks passed. Each model arm has 27 thermal samples; recorded power modes/caps remain high / 190 W and recorded temperatures stay below the runner's absolute ceilings. This is sampled telemetry, not continuous thermal proof.

Rates are recomputed from native prompt/decode milliseconds. Means average the two A rates and two B rates; gain = 100 × (B_mean / A_mean − 1). Load and request-wall times are separate and are not the gate. All reported means, pair gains, IDs and counter deltas were independently recalculated.

API was not started or qualified by these studies; owned containers were cleaned up. No promotion is claimed. Measurements bind the frozen c183 binary, not a separate public-port build. There is no stock-upstream or new combined-versus-stable comparison, and no broad-workload confidence interval.

Sanitized deliverables: `qsa-topk-fit17-benchmark-results.json` and `check_qsa_topk_fit17_benchmark_results.py`. Private paths, configuration contents and raw logs are excluded. Source hashes identify the original evidence; the validator checks receipt consistency without rerunning hardware tests.

    python3 check_qsa_topk_fit17_benchmark_results.py qsa-topk-fit17-benchmark-results.json --selftest

Validation passed; **18 intentional corruption cases rejected**. No public push was performed while preparing these artifacts.
