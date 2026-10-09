# gfx906 qualified receipts and incremental patch archive

This branch, `bench/gfx906-qualified-results`, is an evidence archive, **not an implementation branch**. Its commit adds only files under `bench/`. Runtime source remains identical to public parent `cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3` (tree `ffef85c8f48094c4d97bdba279e77069d34b2e60`). No production promotion or upstream PR is made by this archive.

## What the measurements establish

- [Empty-PCIe report](results/2026-10-09-gfx906-empty-pcie/empty-pcie-report.md): isolated flag-off/on TG +1.705616%, two matched ABBA pairs, exact 1,024-token parity.
- [Primary-commit report](results/2026-10-09-gfx906-primary-commit/primary-commit-report.md): incremental TG +1.212502% on the already-qualified empty-PCIe stack, two matched ABBA pairs, exact 1,024-token parity.
- The separate pre-primary-overlap full-stack comparison versus the user's stable control measured PP +4.438316%, TG +2.194426%, request latency −3.923748%. This is not stock-upstream performance and is not the sum of isolated patch gains. There is no fresh post-overlap full-stack comparison here.
- 4K checks are single pairs. 200K checks establish capacity and archived-reference exact parity, with no fresh performance control. Two ABBA pairs do not establish statistical confidence or general parity.

## Dependency and reproduction limits

The measured full stack includes qualified **HC/J32, PR1525 dequantization and guarded QSA swizzle**, in addition to the two incremental patches archived here. **Applying only these two patches does not reproduce the headline full-stack measurements.** The archive does not contain a complete independently buildable snapshot of the qualified runtime.

Prototype provenance names `f152172332693c933b8a3104ce193d8a4315c2b4` plus qualified fork-stack changes; that bare commit is not the complete measured stack. Primary commit overlap is based on that qualified stack **after** the empty-PCIe patch. The five affected parent file blobs were verified identical to the public `cfc7eeef` snapshot. This is file-level identity only, not proof that the entire public and prototype trees match. Mechanical application and host-only tests below do not establish runtime equivalence or upstream readiness.

Patch order and SHA-256:

1. `patches/2026-10-09-gfx906/archive-empty-pcie.patch`: `7e41dbdb97df1f451ee7c3b5c70c248995d37c36db9650ab2b49a240004b2174`
2. `patches/2026-10-09-gfx906/archive-primary-commit.patch`: `3c87611bd665e3cd4a3525d1536977e2c7a7b8ce22730fc8fa4c8ea36f532d90`

The primary patch is the corrected dual-backend-macro version. Empty-PCIe is enabled with `STRATA_VERIFY_SKIP_EMPTY_PCIE=1`. Primary overlap is enabled by presence of `STRATA_PRIMARY_COMMIT_OVERLAP`; a value of `0` still enables it. Presence of `STRATA_COMMIT_SYNC` forces baseline. Leave diagnostic tracing unset for performance measurements.

## Offline receipt validation

From this branch's checkout root, with Python 3:

```sh
python3 bench/check_gfx906_empty_pcie_results.py bench/results/2026-10-09-gfx906-empty-pcie/empty-pcie-results.json --selftest
python3 bench/check_gfx906_primary_commit_results.py bench/results/2026-10-09-gfx906-primary-commit/primary-commit-results.json --selftest
```

Both passed during archive preparation, including six rejected corrupted receipts each. The empty-PCIe validator checks the isolated experiment, qualification and route/API fields; it does not independently validate the separate `combined_vs_stable` section. All original output-ID arrays are preserved in the JSON. API summaries use an explicit whitelist. Source receipt names are provenance labels, not promises that every original raw file is separately present. Recorded publication/restoration fields describe the original receipt-time state.

## Host eligibility test without modifying the archive checkout

Requires Git, Python 3 and a C++17 compiler. Run from the archive checkout root. This applies patches only to a new temporary detached worktree, runs the extracted actual eligibility block with mocked device calls, then removes that temporary worktree. It does not compile the engine or access a GPU.

```sh
archive_root="$PWD"
tmp="$(mktemp -d)"
git worktree add --detach "$tmp/source" cfc7eeef09730fb83c3e0136c9f6e2251cdd1ca3
(
  cd "$tmp/source" &&
  git apply --unidiff-zero "$archive_root/bench/patches/2026-10-09-gfx906/archive-empty-pcie.patch" &&
  git apply "$archive_root/bench/patches/2026-10-09-gfx906/archive-primary-commit.patch" &&
  python3 "$archive_root/bench/test_primary_commit_guard.py" "$tmp/source"
)
status=$?
git worktree remove --force "$tmp/source"
rmdir "$tmp"
exit "$status"
```

The same patch sequence was checked on the five verified public-parent blobs plus the public `gfx_arch.hpp` header during archive preparation: 63 compiled mocked cases passed, 21 each for gfx906 compatibility, native HIP and unsupported-backend definitions. A full fresh worktree was not materialized during this preparation. This is host/source evidence, not GPU fault injection, runtime qualification or a new performance run.


## QSA reduce12: qualified frozen-stack increment (2026-10-09)

[Final report](results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-report.md) · [full receipt/token IDs](results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-results.json).

Native 64K + 1,024 outputs: candidate PP **646.536120 tokens/s**, TG **53.106939 tokens/s**; incremental **+3.440197% PP / +1.581280% TG** versus the retained qualified HC/J32/dequant/QSA/empty-PCIe/primary-overlap stack. Both matched ABBA pairs are positive and all 1,024 IDs match. 4K, 200K capacity/archived parity, and API checks passed; 4K is a single pair and 200K has no fresh performance comparison. This is not a new combined-versus-stable measurement. The separate micro result is component latency reduction, not model throughput gain.

Release `gfx906-qualified-20261009-reduce12`, binary SHA256 `ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9`, is **not promoted**; live API remains stablece. Both frozen-base and public-1f555 patch artifacts are linked in the report. Public-source port is only source-reviewed/apply-checked, with no separate full upstream build or runtime qualification claimed. The archive still changes only `bench/`, not runtime sources or PR1661. Earlier two-patch reproduction limits above continue to describe the earlier archived experiments; the new patch alone likewise does not recreate its full qualified stack.

From this archive checkout root:

```sh
python3 bench/check_gfx906_reduce12_results.py bench/results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-results.json --selftest
```

The offline validator passed and rejected all 15 corruption cases. This verifies receipt consistency, not a new hardware run. Raw token-ID arrays and the historical micro report/receipt are preserved. [Future public-source probe instructions](results/2026-10-09-gfx906-qsa-reduce12/PROBE-REUSE.md) are not executed results.


## New direct combined and public-component evidence

[Numeric report](results/2026-10-09-gfx906-direct-ff34-vs-ce/README.md): direct whole-combined-versus-optimized-stable 64K/1,024 ABBA gives **+8.101919% PP / +5.049872% TG**, with all four complete token-ID arrays equal. This supersedes the historical absence of a fresh post-overlap combined comparison above. It is not stock-upstream performance or isolated reduce12 attribution. The new public derivative omits private filesystem and service-configuration provenance; its exact validation limits are stated in the report.

[Public reduce12 component receipt](results/2026-10-09-gfx906-qsa-reduce12/public-component-numeric.json) separately records both-GPU full-output parity, ISA and **26.728519% / 26.510032% component latency reduction** for the exact public QSA translation unit with a frozen support archive. This advances the earlier source-only public-port status, but is not a full public-tree build or public-port model qualification.

The separate [implementation commit](https://github.com/0FL01/Strata/commit/08a844d3f31199798b7ea78dc5c8512fd9c17e79) stacks on #1661; the incremental diff is one source file +74/−3. [Prepared upstream PR body](results/2026-10-09-gfx906-qsa-reduce12/PR-DRAFT.md) is available for manual submission after the connector returned HTTP403, `Resource not accessible by integration`. #1661 was unchanged. The archive itself still only changes bench artifacts.


## Scalar FIT17: frozen combined-stack model studies

[Report](results/2026-10-09-gfx906-qsa-fit17/README.md) and [numeric receipts](results/2026-10-09-gfx906-qsa-fit17/qsa-topk-fit17-benchmark-results.json): two separate 64K/1,024-output ABBA studies on the same frozen c183 binary. Suffix-disabled fixed policy gives **+1.413177% TG / −0.001826% PP** with matched counters; ordinary adaptive policy gives **+1.299911% TG / +0.084680% PP** with exact IDs but documented second-pair counter drift. Do not pool these different workloads or attribute the adaptive result to constant work.

All eight full model-output arrays match historical IDs. Separate 4K/200K candidate checks have exact reference IDs and establish correctness only; fallback ownership is explicitly source-inferred, not instrumented. The original component gate failure, historical-counter gate failure and parser infrastructure failure remain preserved. This evidence binds the private combined c183 stack; no public-port build/GPU result or stock-upstream gain is claimed here. No implementation branch or existing PR body is changed by this archive update.

Run from this checkout root (or run the report's relative command after entering its directory):

```sh
python3 bench/results/2026-10-09-gfx906-qsa-fit17/check_qsa_topk_fit17_benchmark_results.py bench/results/2026-10-09-gfx906-qsa-fit17/qsa-topk-fit17-benchmark-results.json --selftest
```

Offline consistency validation passed, including 18 rejected corruption cases. Full numeric IDs, source hashes and failure evidence are retained; private host paths, configuration contents and raw logs are excluded.


### FIT17 public selector component follow-up

[Separate public component report](results/2026-10-09-gfx906-qsa-fit17/PUBLIC-COMPONENT.md): 54 processes completed on both gfx906 devices, with 46 correctness and 8 ABBA timing processes. Direct public selector TU/headers, no support archive. Captured-layer selector latency reduction is **25.7331752864% / 26.0592091451%**; the original 30% discovery gate remains failed. Exact public/private selector ISA comparison and scratch/spill caveats are documented. This advances component qualification only, not a full public-tree build or public-port model result. Existing numerical model receipts remain unchanged.


## Complete c183 stack versus optimized stable ce

[Direct benchmark report](results/2026-10-09-gfx906-direct-c183-vs-ce/README.md): fresh-process 64K/1,024-output A1/B1/B2/A2 gives **+8.147793% PP / +6.509285% TG** against already optimized stable ce. Both pairs are positive; all complete IDs, topology and available aggregate counters match. Unavailable optional counters stay null. Timing-trained adaptive policy means observed counter equality is not proof of constant work. This is a direct whole-stack comparison, separate from ff34-versus-ce; no gains were summed and no stock-upstream or isolated-selector attribution is made. The receipt validator passed 14 corruption tests. Earlier artifacts remain unchanged.


## WIDE51: parked isolated real-200K selector experiment

[Report](results/2026-10-09-gfx906-wide51/README.md) and [numeric metrics](results/2026-10-09-gfx906-wide51/metrics.json): one fresh-process ABBA per physical gfx906 GPU measured **1.654291% / 0.588942% lower isolated selector latency** on the two actual 200K captures. All 12 correctness/timing processes passed parity and safety checks. WIDE51 is parked as an engineering prioritization decision; there was no predeclared speed threshold. One ABBA per device does not establish statistical significance or broad repeatability. No model-throughput or tokens-per-second gain is claimed; capture payloads remain private.
