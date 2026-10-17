#!/bin/bash
set -euo pipefail
HIPCC=/opt/rocm/llvm/bin/clang++
cmake -S /work/source -B /work/build -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER="${HIPCC%++}" -DCMAKE_CXX_COMPILER="$HIPCC" -DCMAKE_HIP_COMPILER="$HIPCC" -DCMAKE_HIP_ARCHITECTURES=gfx906 -DSTRATA_HIP_GFX906=ON -DSTRATA_GGML_DIR=/llama -DSTRATA_BUILD_TESTS=ON
cmake --build /work/build -j2 --target strata
