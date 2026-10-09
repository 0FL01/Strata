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
