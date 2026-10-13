# Historical ABI build and reproduction

## Verified build

The CPU-only build reproduced the exact `74aa76d4…` baseline binary before applying the candidate source. It compiled four baseline host translation units and the same four candidate translation units:

- `src/program/generate.cpp`
- `src/core/conversation_state.cpp`
- `src/core/conversation_file.cpp`
- `src/core/conversation_snapshot.cpp`

The latter three are structure-owning engine archive members affected by the checkpoint/SavedConversation metadata layout. Rebuilding only generate.cpp would risk an ABI/ODR mismatch. The historical state implementation copies checkpoint vectors normally, so role and provenance fields survive that copy; stage split/merge explicitly validates/copies metadata.

The complete historical inventory included 72 original dependency records. The build checked affected ownership, exact baseline object reproduction, all untouched archive member hashes, candidate dependency coverage and link symbol ownership. Only the three reviewed engine archive members were replaced; no GPU kernel translation units were compiled. Donor inputs, the qualified GPU object, package and untouched source bytes stayed unchanged. Four assertion-enabled CPU tests passed.

The pinned ROCm image is `sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646`. The build used no GPU device mounts, no network, two CPUs, a 12 GiB memory/swap cap, 512 PIDs, a read-only container root and dropped capabilities. This 12 GiB build-container limit is unrelated to the runtime's 16 GiB optional-cache ledger.

## Public files and provenance

`build/build_cache16.py` and `build/prior_recipe.py` preserve the exact reviewed build algorithm. `build/package.template.json` records source/build closure and hashes, with host paths replaced by public `/srv/...` examples. `build/dependencies.json` and `build/source-type-audit.json` preserve the reviewed closure evidence. The complete original runtime patch and source hashes are in `runtime/` and `source-pins.json`.

This public directory is not the sealed executable build package. It deliberately omits private host configurations, prompt material, large original source snapshots, model files and donor binaries. The source baseline is the exact historical generate SHA256 `614034787daa9e5c9a114dc36845cea821f01f44a84b7d1aa2fb6597fd0c671e`, not commit 236a6aa's generate.cpp. Candidate generate SHA256 is `f4f542c8b2fbadcbb09ee1a35cbf5de1206a07cbd6e3bdcc78c7a22692863c04`.

For a real rebuild, obtain the pinned historical source/dependency/donor closure and original receipts, reconstruct a fresh sealed package with the recorded relative layout, verify every input hash and set verified host paths in the package manifest. Recompute the package's SHA256SUMS digest after any path change. The builder intentionally refuses unreviewed source/header owners, mismatched old receipts, changed original dependencies, stale archive layouts or a modified sealed package. Do not bypass those checks to use current main.

Exact original receipt hashes and sanitized public-receipt hashes are stored together in `evidence/cpu/provenance.json`. Sanitized receipts are audit copies, not replacements for original receipts in a sealed build. The root publication `SHA256SUMS` validates this public directory only; it is not the build-package digest.

## CPU-only local rerun

Run `python3 -B tests/run_cpu_tests.py` from this directory. It compiles the exact public policy, ledger, metadata and runtime-contract tests against the exact candidate headers, then runs the protocol suite using a generated synthetic seed in a temporary directory. No GPU or model is used.

The preserved source-order test requires separately materialized exact historical baseline and candidate generate.cpp files at the original relative test layout. Those large source snapshots are not in this public bundle. Its original result, and an independently checked exact-patch reconstruction, are recorded in validation evidence.

## Separate v2 package

The v2 source is independently pinned in `runtime-v2/source-pins.json`; its exact v1-to-v2 patch reconstructs generate SHA256 `f08929af779cc1d1fb6ac94d5a4adc1218ba091cf512ec69b146db887df88a5f`. Headers and build algorithm are unchanged. Its sealed package digest is `caf8d1a4724b82cece8103d6c2e3ac5a770f62819f44b2ad7425bc7dda8db0fa`. A new recent-retention test is included. The v1 CPU/GPU receipts do not certify this new source. Its own v2 CPU receipts now pass: exact baseline reproduction, eight host compilations, five CPU tests, unchanged qualified GPU objects/donors and owned cleanup. Binary SHA256 is `2cbcd0eafb1385e4a345bb405e8c677e9fb77f3cbba46088d04c760fdd246ef2`, size21669776 bytes. Original build-receipt SHA256 is `715975c24244ae01718a6c79c4749b7c856d469288b7427b71f8c3866d03dc88`. See `evidence/cpu-v2/`; v2 GPU test results are now available separately: the test gate passed, but deployment is on hold for ancestor-return latency. Current-main/upstream integration remains pending.
