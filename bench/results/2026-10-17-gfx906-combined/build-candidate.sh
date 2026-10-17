#!/bin/bash
set -euo pipefail
HIPCC=/opt/rocm/llvm/bin/clang++
cmake -S /work/source -B /work/build -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER="${HIPCC%++}" -DCMAKE_CXX_COMPILER="$HIPCC" -DCMAKE_HIP_COMPILER="$HIPCC" -DCMAKE_HIP_ARCHITECTURES=gfx906 -DSTRATA_HIP_GFX906=ON -DSTRATA_GGML_DIR=/llama -DSTRATA_BUILD_TESTS=ON -DSTRATA_GFX906_HC_BF16_N4=ON -DSTRATA_GFX906_HC_F16_EXACT=ON
cmake --build /work/build -j2 --target strata native_grouped_parity native_expert_bench qsa_topk_parity hc_bf16_n4_parity hc_f16_exact_parity hc_bf16_n4_owned_test hc_f16_exact_owned_test hc_f16_exact_checks_test
