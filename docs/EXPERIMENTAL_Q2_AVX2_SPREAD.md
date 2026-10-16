# cpu: opt-in exact Q2_0 AVX2 unpack spreading

## Summary

Adds STRATA_Q2_AVX2_SPREAD=1 for the non-VNNI AVX2 Q2_0 row path. This is a CPU optimization, independent of GPU architecture. It originated in a Xeon E5-2698B v3 + two gfx906 system; it must not be advertised as a gfx906-only GPU change.

The integer unpack widens eight packed bytes into 32-bit lanes and spreads each byte's four 2-bit codes into byte lanes. Both implementations instantiate the same q2_avx2_rows.inl: dot products, scale multiplication, FP32 FMA order, correction, and final reduction are unchanged.

## Scope and dispatch

- Default disabled. Only the exact environment value "1" enables it, read once at process startup.
- Existing AVX-VNNI dispatch precedes the option and returns unchanged.
- Existing AVX512 selection outside this translation unit is not modified.
- Only nblocks 10 or 40, positive token groups not divisible by four.
- Full four-token groups retain the old kernel. Only the remainder uses spread.
- Unsupported geometry stays on the existing kernel.
- Existing STRATA_Q2_BITPLANE path remains higher priority through the unchanged outer dispatcher.
- No GPU source, runtime device dispatch, CUDA/HIP/SYCL build definitions, or public API changes.
- Experimental local paired-row kernel is deliberately omitted.

## Duplicate reconnaissance

Pinned upstream main: 296b59d2f73c8f04a805df29c2fa97655adace78.

No direct STRATA_Q2_AVX2_SPREAD implementation/PR found in the targeted 2026-10-16 reconnaissance. Related #257 (two-block unpack) and #706 (bitplane rows) differ; #1949 changes kq_avx1/kq_avx2, not this q2_avx2 path. Existing bitplane code is preserved.

## Tests actually run

Standalone numerical C++ test includes the actual changed production translation unit and pinned public headers, with a test-local CPU feature detector. No numerical implementation is copied or substituted. Production CPU ISA discovery is not linked into this test.

GCC 14.2.0, Linux x86-64 container, -O3 -mavx2 -mfma -mf16c:
- 9,053,525 checks per invocation, all passed.
- Every packed byte value at each of 16 positions and 32 address offsets; both old SIMD unpack and independent scalar unpack oracle.
- Every packed quartet and all signed int8 activation values against scalar dot products.
- Actual plain/spread row kernels and opt-in dispatcher, bitwise float comparison.
- nblocks 1,2,9,10,11,39,40; token widths 1..13; row counts 1,2,3,17,640; nonzero row origins, padded rows, unaligned weights and output sentinels.
- FP16 scales include positive/negative zero, subnormal, normal, negative and maximum finite values; random activation values including -128 stress inputs; deterministic seed.
- Unset, empty, "0", "true", "1x" all remain disabled; exact "1" enables.
- STRATA_AVXVNNI=1 build passed and plain path ran. This host does not expose AVX-VNNI; actual VNNI execution was skipped.
- AddressSanitizer + UndefinedBehaviorSanitizer passed. LeakSanitizer was disabled because ptrace prevents its operation in this environment.

No CUDA/HIP/SYCL engine build, AVX512 dispatch integration execution, AVX-VNNI hardware execution, full model correctness or performance run was performed for this port. These remain qualification work before promoting the optimization/default.

## Performance claim

An earlier single-removal screening experiment on the older combined local stack showed roughly +0.9% TG when this option was retained. That result is only motivation: it is not a benchmark of this clean port, does not establish a statistically confirmed standalone gain, and is not additive with other optimization percentages.

This PR should remain draft until same-day target-CPU baseline/candidate measurements and full backend integration checks are attached.


## Dispatch census added after independent review

The separate Python test extracts the actual option initializer and dispatcher from the candidate source, compiles them with recording row-function spies, and verifies which calls occur. This is control-flow validation, not numerical or ISA-hardware validation.

- 18 configurations: VNNI compiled off/on, each with unset, empty, "0", "1", "true", "1x", "01", " 1", "1 ".
- 224 cases per configuration: nblocks 0,1,9,10,11,39,40,41; nt 0..13; VNNI request false/true.
- Checks exact selected row function, group size, activation/output pointer offsets, row bounds, weight pointer, row stride, and block count.
- Enabled AVX2-only build executes 40 spread-tail spy calls; VNNI-enabled build executes 20 spread-tail calls and 112 VNNI early returns.
- Four deliberate mutations (dead spread branch, lost VNNI early return, missing shape guard, tail redirected to plain) are rejected.
- Production patch unchanged; test uses no production instrumentation.

## Additional target-host validation (2026-10-16)

Repeated the eight numerical test invocations on the target Xeon E5-2698B v3 in the retained ROCm build image: all passed, 9,053,525 checks each. AVX-VNNI runtime support is absent on this CPU; the VNNI-enabled binary exercised its AVX2 fallback. ASan/UBSan passed.

The actual-dispatch extraction test also passed on that host: 18 configurations × 224 cases, plus four intentionally broken dispatch mutations that were all rejected. This uses spy row functions to verify routing without requiring VNNI hardware.

From the repository root:

```sh
g++ -O3 -std=c++17 -mavx2 -mfma -mf16c -I include tests/q2_avx2_spread_test.cpp -o /tmp/q2-spread-test
env -u STRATA_Q2_AVX2_SPREAD /tmp/q2-spread-test off
STRATA_Q2_AVX2_SPREAD=1 /tmp/q2-spread-test on
python3 tests/test_q2_spread_dispatch.py
```

This remains opt-in and draft. Whole-engine integration, target-CPU performance and actual VNNI/AVX512 hardware coverage remain pending.
