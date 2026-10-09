# gfx906: add opt-in QSA reduce12 score reduction

## Summary

Depends on [#1661](https://github.com/Niko1221/Strata/pull/1661), at `1f555de86254cc01ec06882c70f9584c1f09ec39`. This follow-on changes score reduction in its INT8 query-swizzled batched QSA path: twelve warp sums become one reduce-scatter with the same butterfly pairings, reducing score shuffles from 60 to 16. Softmax, value accumulation, merge and the published pre75/DPP implementation are unchanged.

This adapts the [existing `reduce12<DPP>` reduce-scatter and head-of-lane mapping in main](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/src/kernels/cuda/qsa_decode_attn.cu#L230-L283) to gfx906. The algorithm already exists in the pre75 implementation; its normal HIP build guard excludes gfx906. That implementation is untouched.

Default-off. Set `STRATA_GFX906_ATTN_QUERY_SWIZZLE=1` and `STRATA_GFX906_ATTN_REDUCE12=1`, with lane-cell scoring disabled. The new flag requires exactly `1`. Dispatch retains #1661's current-device gfx906/wave64 guard and INT8 restriction. `STRATA_GFX906_ATTN_REDUCE12_TRACE=1` reports actual selection once per host thread. Cached environment settings require separate processes for A/B.

## Public-source component validation

The exact public QSA translation unit and unchanged `bench/gfx906_qsa_query_swizzle_probe.cpp` were compiled and linked against the frozen support archive, with its old QSA object removed. Symbol/link-map checks confirm the new object supplies QSA; the original archive is unchanged. This is an isolated component build, not a full public-tree build.

- Full production QSA chunk + merge, `n_q=32`, context 65,536, 50 timed repetitions per process, A1/B1/B2/A2: GPU 0 mean process medians 1.0384395 → 0.7608800 ms, **26.728519% lower latency**; GPU 1 1.0323620 → 0.7586825 ms, **26.510032% lower latency**. These are component latency reductions, not model TPS gains.
- All four full output files match on both GPUs, including cross-GPU comparison. `n_q=1/context=4` and masked-page `n_q=33/context=4096` also pass full-output parity. The probe checks finite/written outputs, guards and first/final invocation equality. Separate trace smokes confirm actual reduce12 selection; timing arms have trace disabled.
- Actual compiled full-kernel shuffles 70 → 26; score shuffles/adds 60 → 16; full FMACs 87 → 87, score FMACs 84 → 84. VGPR 42 → 48, SGPR 42 → 43; occupancy four waves/SIMD, LDS 15,872 bytes, zero scratch/spills.
- Public source SHA-256: `ec0a11258848d6e2bf6ca0bbe463f06eada460a72be10ff5bb4dce065abe3ab0`. Probe binary: `eff7174652dccc4129ab719e4425c288f93379fd43f3bc59faa758236ecd5f28`.

Tests use two gfx906 wave64 GPUs, pinned build image `sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646`, patched AMD Clang `23.0.0git`, and `-O3 -DNDEBUG -std=c++20 --offload-arch=gfx906`. The stable API was restored healthy with the same executable; no configuration change or production promotion occurred.

## Frozen-stack model evidence

Whole-model 65,536-token prompt / 1,024-output A/B/B/A: PP 625.033728 → 646.536120 tok/s (**+3.440197%**); TG 52.280242 → 53.106939 tok/s (**+1.581280%**). Individual pairs: PP +3.43809% / +3.44230%, TG +1.61839% / +1.54418%. All 1,024 output IDs match across the four arms.

These model results toggle only reduce12 on the frozen qualified8900 experimental stack: base `f152172332693c933b8a3104ce193d8a4315c2b4` plus HC, J32/grouped-MMQ, dequantization, query swizzle, empty-PCIe and primary-commit changes. Both arms retain `STRATA_PRIMARY_COMMIT_OVERLAP=1`; trace is off. Those host optimizations are measurement context, excluded from this implementation patch. This is separate from the public component build above.

That frozen reduce12 candidate also passed a 4,096-token / 1,024-output pair (+3.070518% PP, +1.328129% TG, all IDs exact), 200,000-token / 256-output capacity/parity (616.858242 PP, 45.537017 TG, exact archived-reference IDs), and targeted tools, two vision trials, cache restoration, auth/UI and disconnect/cancel checks. The 200K run has no fresh performance control. Earlier raw-score micro parity remains diagnostic evidence; no score-only kernel or test macro is added to production.

[Archived report and receipts](https://github.com/0FL01/Strata/blob/44a92d54e192ca8554c534fc2f2673e8b2a904b5/bench/results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-report.md) document the frozen qualification. No full-model run on the public port, full-tree build, upstream CI pass or general-workload speedup is claimed.

## Reproduce the component check

The unchanged CMake target is `gfx906_qsa_query_swizzle_probe`; it needs the gfx906 HIP backend. The measured build used the isolated object/archive link described above. With the resulting binary in `PROBE`, run each GPU separately:

```bash
mkdir -p results
for gpu in 0 1; do
  for arm in A1 B1 B2 A2; do
    flag=0; [[ $arm == B* ]] && flag=1
    env -u STRATA_GFX906_ATTN_QUERY_SWIZZLE_TRACE \
      HIP_VISIBLE_DEVICES="$gpu" STRATA_GFX906_ATTN_QUERY_SWIZZLE=1 \
      STRATA_ATTN_LANECELL=0 STRATA_GFX906_ATTN_REDUCE12="$flag" \
      STRATA_GFX906_ATTN_REDUCE12_TRACE=0 \
      "$PROBE" 32 65536 50 "results/gpu${gpu}-${arm}.bin"
  done
  for arm in B1 B2 A2; do
    cmp "results/gpu${gpu}-A1.bin" "results/gpu${gpu}-${arm}.bin"
  done
done
cmp results/gpu0-A1.bin results/gpu1-A1.bin
```

Use nonconflicting device-visibility settings. Before timing, run a separate flag-on process with `STRATA_GFX906_ATTN_REDUCE12_TRACE=1` and require `selected=1`. For edge parity, repeat off/on with arguments `1 4 20 output.bin` and `33 4096 20 output.bin --masked-pages`. Compare complete dumps. Average the two A process medians and the two B process medians; latency reduction is `100*(A_mean-B_mean)/A_mean`.

## Integration

This is a stacked follow-on: until #1661 merges, the comparison against upstream `main` also contains its inherited seven-file, two-commit change. The incremental reduce12 commit alone changes the QSA source by +74/−3 lines. #1661's body and implementation history are preserved.

Production changes are confined to `src/kernels/cuda/qsa_decode_attn.cu`, with current fixed `G=12`. Unmerged [#1402](https://github.com/Niko1221/Strata/pull/1402) uses the third kernel template argument for `G`; #1661 uses it for `QUERY_SWIZZLE`, and this adds `REDUCE12` fourth. Integration needs explicit template/dispatch reconciliation and must retain a `G=12` gate until other geometries are separately qualified.
