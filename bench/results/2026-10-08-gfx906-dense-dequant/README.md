# gfx906 measured dead ends and IQ4 XS comparison

Date: 2026-10-08

Updated after PR #1525 clean-slice model measurements completed at 19:44:39 UTC on 2026-10-08.

Q5_K head row grouping R4 is rejected: measured projection latency rose 24.40% despite exact output-byte equality. QSA query-fast grid ordering is parked: combined scorer plus current top-k throughput improved 5.74%, below this experiment's 20% gate. IQ4_XS flat dequantization achieved a 9.803× conversion microbenchmark speedup with matching full-matrix and sliced dumps, but its subsequent 4K model screen improved prompt-processing throughput by only 0.811893%. That misses the 1% screen gate, so no 64K run followed. The subsequent dequantization-only comparison finds PR #1525's h16x8 kernel 3.953480× faster than flat with matching measured dumps. The flat route is superseded as the component candidate; PR #1525's dequantization slice is the component winner with measured raw-byte edge parity. A fresh model test reports +0.806234% prompt-processing throughput at 4K and +1.169800% at 64K, with matching 256-token output-ID sequences within each prompt. These modest model gains do not inherit the component speedup. No production deployment was performed.

## Q5 K head R4 rejected

The probe compares R1 with R4 for `n_in=2560`, `n_out=248320`, and four input columns. The weight buffer is 437,043,200 bytes. Route traces identify 62,080 CTAs for R1 and 15,520 for R4.

Timing uses warmed graph replay in A1/B1/B2/A2 order. Each figure below is one run's median, in milliseconds per projection.

| Run | Rows per CTA | Median ms |
| --- | --- | --- |
| A1 | 1 | 2.79074216 |
| B1 | 4 | 3.47506309 |
| B2 | 4 | 3.47732306 |
| A2 | 1 | 2.79819250 |

The decision averages the two A medians and the two B medians: **2.79446733 → 3.476193075 ms**. This is **24.3956% higher latency** and **19.6113% lower throughput**. The receipt sets `expand_parity=false`; this branch does not advance.

All four runs share input FNV-1a-64 `c15b2c38b3530e55` and an identical 3,973,120-byte output dump:

`4df9c56b70236b9c2c3248abf5c3d2ac1e0bd0d7dd60684bbd7e09f66689caf8`

The receipt reports finite outputs, intact guards, repeatability, and activation immutability. Equality covers the measured input and shape. It is not a universal correctness or model-output claim.

## QSA query fast grid ordering parked

The scorer probe uses context 135,168, 256 queries, active reach 33,793, stride 51,202, and top-k cap 2,051. A uses key-fast grid `(4225,256,1)`; B uses query-fast grid `(256,4225,1)`. The log records 50 repetitions each for scorer and combined scorer plus current top-k timings.

| Run | Grid order | Scorer ms | Scorer plus top k ms |
| --- | --- | --- | --- |
| A1 | key-fast | 7.772 | 10.128 |
| B1 | query-fast | 6.972 | 9.577 |
| B2 | query-fast | 6.971 | 9.584 |
| A2 | key-fast | 7.783 | 10.132 |

The decision's paired-run aggregates are:

- Scorer: **7.7775 → 6.9715 ms**, a **11.5614% throughput gain**.
- Scorer plus current top-k: **10.1300 → 9.5805 ms**, a **5.7356% throughput gain**.

These percentages use baseline time divided by candidate time minus one; they are throughput gains, not latency-reduction percentages. The combined gain misses this candidate experiment's **20% gate**. The receipt sets `clear_signal=false`; retain the result as a measured modest improvement and park the branch.

All four 54,531,365-byte dumps, containing the full warp-score buffer and current top-k IDs, match:

`4bceb2f8c253d8a1596389bb8b7d7cb544d3f42213d920eb4af5fb5f1cbb86fd`

Input FNV-1a-64 is `696ff1be4ec6c7fe`. Buffer canaries pass; current top-k matches the reference for 256/256 queries. Maximum reported score error against FP64 is `2.14e-05` at score scale 256. The tensor-core scorer is unavailable in this probe, and its `sc_new` buffer is a copy used for selector checks. This result establishes parity between the measured grid-order arms, not tensor-core scorer parity or model-level equivalence.

## Dense conversion baseline and budget

The receipt identifies two AMD Radeon Pro VII devices with gfx906 architecture and wave size 64. These are synthetic, contiguous-output, conversion-only tests with five warmups and 20 repetitions; validation is finite-written values, padding guards, and hashes.

| Role | Format | Rows × columns | GPU 0 median ms | GPU 1 median ms |
| --- | --- | --- | --- | --- |
| gate | IQ3_S | 6144 × 2560 | 0.300879 | 0.300480 |
| qkv | IQ4_XS | 10240 × 2560 | 4.458159 | 4.446159 |
| output | Q8_0 | 2560 × 6144 | 0.181680 | 0.181120 |

For the IQ3_S gate conversion, the budget uses a 103,112 ms stage and 336 calls. Saving 1% of that stage requires 3.068810 ms saved per call; a 2× conversion optimization would require a 6.137619 ms baseline per call. The measured baseline permits only **0.097914–0.098044%** stage savings even if conversion is removed entirely, or **0.048957–0.049022%** with a 2× conversion speedup. This narrow gate-conversion target is too small to provide a meaningful stage improvement under those assumptions. Do not apply that bound to unrelated kernels or unmeasured call counts.

The IQ4_XS baseline is materially larger, motivating the separate candidate below. The budget's checks do not by themselves prove equality against a reference implementation. Both GPUs report matching FNV-1a-64 values per role:

- IQ3_S: `e0d270bdcad470b6`
- IQ4_XS: `61c038143243cbe1`
- Q8_0: `38399a92c09f0b40`

## IQ4 XS flat dequantization component result

This conversion microbenchmark passes its recorded gate. For GPU 0, case 0, averaging the A1/A2 medians gives **4.442042 ms**; averaging B1/B2 gives **0.453120 ms**, a **9.803235×** speedup. This is a conversion-only speedup. The smaller model-screen result below must be evaluated separately.

| Run | GPU | Case | Arm | Median ms |
| --- | --- | --- | --- | --- |
| A1 | 0 | 0 | A | 4.441998 |
| B1 | 0 | 0 | B | 0.453920 |
| B2 | 0 | 0 | B | 0.452320 |
| A2 | 0 | 0 | A | 4.442086 |
| gpu0_case1_A | 0 | 1 | A | 4.445598 |
| gpu0_case1_B | 0 | 1 | B | 0.453040 |
| gpu1_case0_A | 1 | 0 | A | 4.438640 |
| gpu1_case0_B | 1 | 0 | B | 0.451120 |
| gpu1_case1_A | 1 | 1 | A | 4.450640 |
| gpu1_case1_B | 1 | 1 | B | 0.451600 |

Every corresponding A/B dump is 52,429,010 bytes and matches by case across both GPUs. The case identifiers are retained as recorded; their input-generation definitions are not included in the receipt.

### Sliced parity

The sliced probe covers two GPUs, two cases, and slice-row settings of 10,240, 6,553, and 1,279. All 24 runs retain the same per-case dump size and SHA-256 as the full-matrix runs.

| GPU | Case | Slice rows | A median ms | B median ms |
| --- | --- | --- | --- | --- |
| 0 | 0 | 10240 | 4.433597 | 0.453840 |
| 0 | 0 | 6553 | 4.362158 | 0.457600 |
| 0 | 0 | 1279 | 4.026960 | 0.493119 |
| 0 | 1 | 10240 | 4.448798 | 0.452880 |
| 0 | 1 | 6553 | 4.353038 | 0.457040 |
| 0 | 1 | 1279 | 4.006400 | 0.493280 |
| 1 | 0 | 10240 | 4.448078 | 0.451600 |
| 1 | 0 | 6553 | 4.322721 | 0.456640 |
| 1 | 0 | 1279 | 4.028240 | 0.492480 |
| 1 | 1 | 10240 | 4.453120 | 0.452000 |
| 1 | 1 | 6553 | 4.359920 | 0.456640 |
| 1 | 1 | 1279 | 4.017840 | 0.492720 |

Shared dump SHA-256 values:

- Case 0: `3c50f1d45992f7b9e5f0072f1c2bd21fdd5155087289228227a9a0ec90269be3`
- Case 1: `0d575e07394c0f71d2be8decbba8484eadff0a10f4c4e99f5725813c9a563de4`

The full-matrix and sliced receipts report `passed=true`. These checks support equality for the tested fixtures and slicing configurations. They do not alone establish parity for arbitrary inputs, model logits, generated tokens, or end-to-end inference.

The verified scratch capacity is **64 MiB**. The full 10,240 × 2,560 FP16 QKV output is 52,428,800 bytes (50 MiB), so the entire matrix fits. The 52,429,010-byte figure above is the recorded dump-file size, not scratch demand.

## IQ4 XS 4K model screen below the gate

The screen compares candidate flag 0 (A) with flag 1 (B) on the **HC+MMQ-qualified base identified as `17b688`**, using the same new `strata` binary in both arms:

`8ac058d275828e6cc09ab8603040016508a6f20284f3e9970b86074eecfd3ac4`

It does **not** compare against the production `ce` baseline. Treat the result as the incremental candidate effect on the qualified HC+MMQ base.

The A1/B1/B2/A2 screen uses a 4,096-token code prompt, int8 KV, and 256 generated output IDs per run. Sampling is greedy (`temperature=0`, `top_p=1`, `top_k=1`, seed 12345); all runs report zero reused prompt tokens and 4,096 prompt tokens read.

| Run | Prompt ms | Decode ms | PP tokens per second | TG tokens per second |
| --- | --- | --- | --- | --- |
| code4096-A1 | 11301.4 | 4680.0 | 362.432973 | 54.700855 |
| code4096-B1 | 11209.9 | 4672.6 | 365.391306 | 54.787484 |
| code4096-B2 | 11206.8 | 4672.0 | 365.492380 | 54.794521 |
| code4096-A2 | 11297.3 | 4671.6 | 362.564507 | 54.799212 |

Averaging the two PP rates in each arm yields **362.498740 → 365.441843 tokens/s**, or **+0.811893%**. This is below the **1% PP screen gate**. All four runs pass, and all **256 output IDs match across every run**. This is equality for one measured prompt and sampling setup; logits, arbitrary prompts, and broader quality are not validated.

PP uses the reported full prompt count divided by native prompt time, with the last prompt token executing in the first decode window. TG uses actual outputs divided by native decode time. Loading and request wall time are separate; the 0.811893% figure is not a whole-request or total-model gain. It is also not a production-baseline improvement.

The receipt marks `screen_only=true` and finishes at `2026-10-08T19:22:10.648736+00:00`. The failed screen gate means **no 64K run**. This screen applies to the flat candidate only. The separate, subsequently completed PR #1525 model measurements appear below.

## PR 1525 dequantization slice supersedes flat

The competing implementation comes from [PR #1525](https://github.com/Niko1221/Strata/pull/1525), pinned to commit `52de5c0a31ab25a5c4d73ea6a1c39b3d1bfa7236`. This comparison tests the **dequantization slice only**, specifically the IQ4_XS h16x8 path. This IQ4_XS timing comparison does not test or qualify the whole PR or its fusion changes. Separate IQ4_XS and Q8_0 edge tests are recorded below.

The extracted dequantization patch SHA-256 is:

`97137b72294b5b071c56398146d27edec1dbc206d055992e45ab129f78cfe239`

In this receipt, **A is PR h16x8 and B is the existing flat kernel**. The arm labels are local to this experiment and differ from the original group32-versus-flat experiment.

| Run | GPU | Case | Kernel | Median ms |
| --- | --- | --- | --- | --- |
| A1 | 0 | 0 | PR h16x8 | 0.114400 |
| B1 | 0 | 0 | flat | 0.452000 |
| B2 | 0 | 0 | flat | 0.452240 |
| A2 | 0 | 0 | PR h16x8 | 0.114320 |
| gpu0_case1_A | 0 | 1 | PR h16x8 | 0.114400 |
| gpu0_case1_B | 0 | 1 | flat | 0.452080 |
| gpu1_case0_A | 1 | 0 | PR h16x8 | 0.114160 |
| gpu1_case0_B | 1 | 0 | flat | 0.452000 |
| gpu1_case1_A | 1 | 1 | PR h16x8 | 0.114080 |
| gpu1_case1_B | 1 | 1 | flat | 0.451600 |

GPU 0, case 0 paired-run means are **0.114360 ms for PR h16x8** and **0.452120 ms for flat**: h16x8 is **3.953480× faster than flat**. The receipt's `speedup=0.25294169689462975` is the inverse ratio, PR time divided by flat time; it should not be read as a regression.

All ten runs across both GPUs and both cases have identical corresponding 52,429,010-byte dumps. Their SHA-256 values match the case 0 and case 1 values already reported for the original group32 reference and flat implementation. The receipt identifies this as an original-group32 full-byte reference comparison and reports `passed=true`. Equality remains limited to these measured fixtures.

**Decision:** supersede the campaign's flat route with PR #1525's dequantization slice as the component winner. The model measurements below establish a much smaller prompt-processing gain for the tested cases; production readiness is not established.

The subsequent edge qualification below resolves the signed-zero oracle issue without normalizing the raw baseline/candidate dumps. The subsequent model measurements are reported below.

## PR 1525 edge qualification

The baseline/candidate edge qualification completed successfully, with the GPU sequence **0 → 1 → 0**. The aggregate receipt records identical **2,007,815-byte raw dumps**:

`281bd2d554ccebb155c2b2908a48eb0145f7f9bf4fe396f94bfe491aa93d7cba`

Each reported all-boundary-case integer oracle check covers **126,976 FP16 values**: **123,968 exact half-bit matches** and **3,008 differences only in the sign of zero**, identically for baseline and candidate. There are no other reported exceptions. The original baseline canonicalizes negative zero relative to the integer oracle; this behavior is already present without the candidate. No cause involving fast-math has been established.

The baseline/candidate raw dumps were **not normalized**. Their equality is stronger than treating signed zeros as equivalent: the candidate preserves the baseline's actual output bits in the measured suite. The oracle result must still be described separately rather than claimed as 126,976 exact bit matches against the oracle.

Padded and unpadded IQ4_XS QKV and Q8_0 output cases pass on both GPUs:

| GPU | Target | Layout | Baseline median ms | Candidate median ms | Dump bytes |
| --- | --- | --- | --- | --- | --- |
| 0 | IQ4_XS QKV | unpadded | 4.446878 | 0.114240 | 52,429,010 |
| 0 | IQ4_XS QKV | padded | 4.515838 | 0.114720 | 53,739,730 |
| 0 | Q8_0 output | unpadded | 0.180880 | 0.066720 | 31,457,488 |
| 0 | Q8_0 output | padded | 0.180800 | 0.067040 | 31,785,168 |
| 1 | IQ4_XS QKV | unpadded | 4.447921 | 0.114080 | 52,429,010 |
| 1 | IQ4_XS QKV | padded | 4.525679 | 0.114640 | 53,739,730 |
| 1 | Q8_0 output | unpadded | 0.182080 | 0.067840 | 31,457,488 |
| 1 | Q8_0 output | padded | 0.181920 | 0.067840 | 31,785,168 |

Each baseline/candidate pair has matching dump bytes and SHA-256. Hashes are also consistent between the two GPUs for each target/layout:

- IQ4_XS unpadded: `3c50f1d45992f7b9e5f0072f1c2bd21fdd5155087289228227a9a0ec90269be3`
- IQ4_XS padded: `7ce6243272f4f549699fb74441bd31c1f403f5219194d6530060989536029eb6`
- Q8_0 unpadded: `4aa26c0fb69fef1bc3d8812f1ac13cc1d38ec4f5d124da658d66a9edd1382661`
- Q8_0 padded: `20134debbe0bc19d354c44bea2610567f2bd129d1c1a73d79d978ab324be7fc8`

The receipt reports `passed=true` and successful API restoration. This qualifies the measured dequantization edge suite; it does not establish model-level improvement or qualify unrelated changes from PR #1525.

## PR 1525 model measurements

The completed test isolates the **clean PR #1525 dequantization slice**, credited to [PR #1525](https://github.com/Niko1221/Strata/pull/1525), with candidate engine SHA-256:

`849ad4035552455425331ae55e844f90f2c3238b39fd5deb87e54441b8f49c28`

A is the original-dequantization baseline; B is the upstream dequantization-slice candidate. This is an incremental comparison on the qualified HC+MMQ base, not a comparison against the production `ce` baseline. The remaining PR fusion changes are outside this test.

The predeclared plan was a fresh **4K A1/B1/B2/A2 screen**, followed by a **64K pair if the screen gain exceeded 0.5%**. That threshold was set before measuring this upstream implementation. It is separate from the older flat-route screen's 1% gate and does not reinterpret that result. The new 4K screen passed its gate, and the 64K pair ran in B1/A1 order.

| Run | Prompt ms | Decode ms | PP tokens per second | TG tokens per second |
| --- | --- | --- | --- | --- |
| code4096-A1 | 11297.1 | 4682.2 | 362.570925 | 54.675153 |
| code4096-B1 | 11209.0 | 4678.2 | 365.420644 | 54.721902 |
| code4096-B2 | 11215.8 | 4682.7 | 365.199094 | 54.669315 |
| code4096-A2 | 11308.5 | 4669.8 | 362.205421 | 54.820335 |
| code65536-B1 | 106035.2 | 4896.6 | 618.058909 | 52.281175 |
| code65536-A1 | 107275.6 | 4900.9 | 610.912454 | 52.235304 |

- **4K:** mean PP rate **362.388173 → 365.309869 tokens/s**, a **+0.806234%** gain from four ABBA runs.
- **64K:** PP rate **610.912454 → 618.058909 tokens/s**, a **+1.169800%** gain from one B/A pair.
- **64K decode:** TG changes **52.235304 → 52.281175 tokens/s**, only **+0.0878%**. Treat this as noise; one pair does not establish a meaningful decode gain.

All six runs pass. All **256 output IDs are identical across the four 4K runs**, and all **256 IDs match within the 64K pair**. This is within-prompt equality, not equality between different prompt lengths. All runs use int8 KV, greedy sampling, seed 12345, zero reused prompt tokens, and the full stated prompt count. The PP/TG definitions and last-prompt-token accounting are the same as in the flat-route screen. These are prompt-phase throughput measurements, not total-request or model-wide speedup factors.

The receipt finishes at `2026-10-08T19:44:39.380017+00:00` and records successful restoration of the baseline API. It retains `screen_only=true`; its six recorded results explicitly include the 64K pair. **A 200K test and a candidate API smoke test were not run.** Baseline API restoration does not validate the candidate API. Wider prompt coverage, logits, quality, long-context stability, and repeated 64K performance remain unqualified. **No production deployment was performed.**

## Reproducing the published edge checks

The publication target is `0FL01/Strata`. The published source includes the credited upstream dequantization slice and the edge probe. The component timing/comparison probe was tested locally but is not included in this publication, so the historical component measurements are **not a self-contained reproduction package**.

Prepare local `baseline/` and `candidate/` worktrees following the repository's HIP setup and pinned llama.cpp instructions. Put the **same published edge probe and CMake target definition in both trees**. The baseline must retain the publication parent's original dequantization source; the candidate contains only the credited PR #1525 dequantization slice. Run from their common parent directory in the configured ROCm environment:

```sh
set -eu
mkdir -p repro-output
OUT=$(cd repro-output && pwd)

for tree in baseline candidate; do
  cmake -S "$tree" -B "$tree/build-906" -DSTRATA_HIP_GFX906=ON
  cmake --build "$tree/build-906" --target gfx906_iq4xs_edge_probe -j4
done

pass=0
for device in 0 1 0; do
  for tree in baseline candidate; do
    "$tree/build-906/gfx906_iq4xs_edge_probe" \
      --device "$device" --dump "$OUT/edge-$pass-$tree.bin"
  done
  cmp "$OUT/edge-$pass-baseline.bin" "$OUT/edge-$pass-candidate.bin"
  pass=$((pass + 1))
done
sha256sum "$OUT"/*.bin
```

Compare raw dumps with `cmp`; do not normalize signed zeros. Keep the same build setup, inputs, and device in both arms. The edge probe is a C++ target linked to `strata_kernels` and the GPU runtime. Its dump argument uses separate tokens, `--dump FILE`. These commands reproduce edge comparisons, not the full historical model or timing campaign.

## Artifact identity and evidence limits

SHA-256 values below identify the recorded builds. The recorded builds report exit code 0.

| Artifact | SHA 256 |
| --- | --- |
| Q5 head R4 patch | `bbaf125096b2592450cf921b3e3035dde7a85771d64863ce228ea33398c939f6` |
| Q5 head R4 probe binary | `97dc0c60acb8851fd095cce8d2dc4730189189d4980dd8464eeddc63cb901b30` |
| IQ4 XS sliced probe binary | `8230b23987d6b5ee206d2d431de319e02eb31c10117b08e2851d14e4f8cea554` |
| IQ4 XS sliced strata binary | `8ac058d275828e6cc09ab8603040016508a6f20284f3e9970b86074eecfd3ac4` |
| Ancillary head phase profile patch | `f804d330a22548379bfba6f08194e311d659892f148fceb38aa67099f6ab6b28` |
| Ancillary head phase profile strata binary | `3f7d1c0bf55e342df7820e2f3a62fb0e827ef907dc352897e5016b077ae8d20d` |

Additional verified build identities supplement the aggregate microbenchmark receipt:

| Artifact | SHA 256 |
| --- | --- |
| QSA grid order patch | `cadf88f1646d3652c06d52cef8a3c3584bbb2f17c7b4f286d6665cab9b21f712` |
| QSA `qsa_select_bench` probe binary | `c9e422b2a3abc5219684586740f460f23a0024d1c49c0853172d81b3df3f0163` |
| Initial IQ4 XS patch | `212de31b5a405c6e94aa3b6f783d40ca69d88d16ba8c69fd0e7302a410263863` |
| Initial IQ4 XS probe binary | `7890a6b7aa41f7276817167ffb42ee4a7a1a542dae44af36dcff34c90633f5b6` |

These four supplemental identities are not embedded in the aggregate microbenchmark receipt. The ancillary head-phase build has no accompanying phase timing result here and must not be attributed to the QSA or IQ4_XS measurements.

Microbenchmark source receipt: `iq4xs-and-deadends-receipts-20261008.json`

Source SHA-256: `6c228a1a26ce3969b4f6dc19cd6dcda00c49f422d180d57c615eaacfb1e82b31`

Model-screen source receipt: `iq4xs-screen-summary-20261008.json`

Model-screen source SHA-256: `1f85685f1573300d298671769d8f80440ac4ff0d7a087199e2b7d790f7e17f44`

PR comparison source receipt: `iq4xs-pr1525-micro-20261008.json`

PR comparison source SHA-256: `99327db720e0fe1bfa49d2572003f3da953d33aef32463792b23437a809b3977`

Edge qualification source receipt: `iq4xs-pr1525-edge-20261008.json`

Edge qualification source SHA-256: `c40686144582f1bc9471716b849f614fb3ec1533eb6fb53657977b2d348be164`

Final PR model source receipt: `pr1525-model-summary.json`

Final PR model source SHA-256: `520c9b80b0f368da33d0c22e7da3477ac0f7f55b706fdbec11a67e4b0d12050e`

Microbenchmark evidence entries are `q5-head-r4/{build,micro/summary}.json`, `qsa-score-grid-order/micro/summary.json`, `head-phase-profile/build.json`, `iq4xs-flat-dequant/micro/summary.json`, and `iq4xs-flat-dequant/sliced/{build,micro/summary}.json`. No new benchmark execution was performed for this report. Host-specific absolute paths, mount arguments, service configuration, and health payload details are omitted. Recorded restoration checks pass after the Q5, QSA, full-matrix IQ4_XS, sliced IQ4_XS, 4K model-screen, PR #1525 microbenchmark, PR #1525 edge, and final PR #1525 model runs; they describe those checkpoints rather than current service state.
