# Measured build provenance

## Local image and toolchain

- Local image content ID: `sha256:bccb7ee7e7a78274519db9a43ba63c34ddd2e74bb60f8764a8f50aaee1f2c646`
- Local image tag: `llama.cpp-gfx906:cmake-4.4.3`
- CMake: 4.4.3
- Compiler: AMD clang 23.0.0git, ROCm/llvm-project commit `46fcb339fb61119b337f973c7ca9e710a319fdd0`, patched with `440716f8b87be9d8e20ed910e10e5b6d14d57cf6`
- Resolved LLVM directory: `/opt/rocm/core-7.14/lib/llvm/bin`
- GGML/llama dependency revision: `3cf03257f219afbe7334045ff7c6a06ac68c627d`

The `core-7.14` directory label is recorded literally. No `/opt/rocm/.info/version` was present; a unified ROCm release number has not been established. In particular, this is not evidence of ROCm 7.1.4.

The image content ID and tag are local identities. No public registry image or reproducible Dockerfile has been verified. These commands document the measured build, but that missing image provenance remains a reproduction limitation.

## Same prerequisites, separate builds

Start both sources from upstream `477ac13cbe8e582c20484871ce459d20d82df09d` and apply `common-build-prerequisites.patch` to both. Apply the measured combined optimization patch only to candidate source. Use separate clean source/build directories. The two HC build options below are candidate-only; runtime opt-ins are separately specified in `CONFIG.example.json`.

Inside the measured image, mount the intended source at `/work/source`, its separate build directory at `/work/build`, and the pinned dependency tree at `/llama`.

Baseline:

    HIPCC=/opt/rocm/llvm/bin/clang++
    cmake -S /work/source -B /work/build -G "Unix Makefiles" \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER="${HIPCC%++}" \
      -DCMAKE_CXX_COMPILER="$HIPCC" \
      -DCMAKE_HIP_COMPILER="$HIPCC" \
      -DCMAKE_HIP_ARCHITECTURES=gfx906 \
      -DSTRATA_HIP_GFX906=ON \
      -DSTRATA_GGML_DIR=/llama \
      -DSTRATA_BUILD_TESTS=ON
    cmake --build /work/build -j2 --target strata

Candidate, using its own source/build mounts:

    HIPCC=/opt/rocm/llvm/bin/clang++
    cmake -S /work/source -B /work/build -G "Unix Makefiles" \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER="${HIPCC%++}" \
      -DCMAKE_CXX_COMPILER="$HIPCC" \
      -DCMAKE_HIP_COMPILER="$HIPCC" \
      -DCMAKE_HIP_ARCHITECTURES=gfx906 \
      -DSTRATA_HIP_GFX906=ON \
      -DSTRATA_GGML_DIR=/llama \
      -DSTRATA_BUILD_TESTS=ON \
      -DSTRATA_GFX906_HC_BF16_N4=ON \
      -DSTRATA_GFX906_HC_F16_EXACT=ON
    cmake --build /work/build -j2 --target strata

Exact nonsecret scripts are included as `build-baseline.sh` and `build-candidate.sh`. The latter also builds the component test targets; its full target list is authoritative.

Build/test target availability is not proof that every component or backend test ran. Keep executed component-test evidence separate from these build instructions.

## Assets and historical metadata

The runtime configuration explicitly supplies the verified Q8_0 PLE second shard through `--ple-gguf`. It overrides the PLE source associated with the earlier expert-pack conversion. That pack's conversion metadata still refers to an old IQ4_NL second shard of 28,800,138,432 bytes; it must not be presented as the current Q8_0 model identity. The actual Q8_0 file is 54,400,261,312 bytes with its separate SHA256 and source revision in `evidence/identities.json`.

MTP readiness metadata identifies `Qwen/Qwen3.8-Flash-Next` revision `de4b8e4d43b917e7706784d8bb445c9af86a3540`, conversion Strata revision `6f32ec070f23ced9f50e704d854d775da52591ab`, experts `q2_0`, validated 2026-10-05. Readiness metadata is provenance, not a replacement for hashes of the actual loaded assets. The 17-file asset hash inventory is in `evidence/runtime-asset-hashes.json`. It was collected after timing, with stable stat checks reported during collection; see `evidence/asset-hash-provenance.json`. These post-run checks are not a pre-run byte snapshot.
