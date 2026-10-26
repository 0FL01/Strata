# Native request bounds: CPU-only correctness checkpoint

Base: f9b38e9e5d70cef7776f2a5bd6fed5e56872ec02. Separate branch; no main or runtime replacement.
This is a correctness change, not a measured speed improvement.

## Change

Check strtol/strtoll overflow and no-digit results for batch headers and ordinary output budgets.
Before batch admission rewrites the output count to one, reject an impossible original budget.
After parsing IDs, validate the complete original batch budget, not the rewritten admission count.
Use short-circuit subtraction checks before signed narrowing, vision position setup, and the
consumed-token vector reserve. The reserve uses the actual int32 vector max_size.
A rejected length does not apply the per-request pipe setting.

GENI already carries expanded image_pad tokens. The native image loader consumes those tokens;
it does not expand their count. The early check protects the position-table traversal as well.
The existing strict int32 token-list parser and accepted permissive header delimiters are unchanged.
Malformed or oversized budgets emit terminal ERR without the retryable BGEN: prefix.
Numerically unavailable/out-of-range or occupied slots retain their existing retryable BGEN: behavior.

## CPU evidence

Run tests/native_request_bounds_cpu.py with Python 3, g++, and the baseline commit available locally.
The script extracts the actual source helpers, batch-admission block, token parser, and ordinary
request prefix; it does not substitute a separately written implementation for those blocks.

- Normal and UBSan builds: 416,863 assertions each, both pass.
- Ten retained 8K/64K valid request packets: all parsed IDs and option fingerprints unchanged.
  The packets remain private and are not included. Supply optional --retained files to reproduce
  this additional coverage; the standalone suite also runs without them.
- Wide arithmetic Cartesian and random checks use an independent __int128 oracle.
- Reserve failures leave their output sentinel unchanged.
- Exact context boundaries cover GEN, GENI, BGEN and BGENI.
- Eighteen captured parser-harness protocol probes pass across both compiler variants:
  permanent versus retryable ERR namespace, no stray DONE from the extracted parser, and
  malformed GEN/GENI followed by valid text parsing in the same harness process.
- Empty, negative and overflowing IDs remain rejected; valid parsing before and after is retained.
- UBSan stderr empty; git diff --check clean.

The extracted harness stubs the pipe setter and batch slot metadata. It stops before image I/O,
device setup, native generation, session/cache transitions, or the Service layer. These results
are NOT evidence of full native-process or Service recovery, image-loader safety, device-token
parity, or a performance improvement. Native build and GPU smoke have not run at this checkpoint.

## Remaining scope

Input line/token-vector allocations and queued transport buffers remain uncapped.
Embedding-file off+cnt arithmetic and allocations are a separate unaddressed concern.
Numeric slot availability keeps legacy retry semantics. Optional sampling-key grammar and
permissive numeric delimiters are not hardened here. No production/public default is changed.

Source SHA-256: c1f7f22d5a4ecdbb33eca530a180f18b233a2efee10b7d6e6d53ef7ffea1b097.
Test-generator SHA-256: d6e5d7cb37affff0d44018b8d504689315fa2aff9a7d11614d03d5319ee4dc2d.
