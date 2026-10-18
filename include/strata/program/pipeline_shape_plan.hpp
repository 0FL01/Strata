#pragma once
// Host-only planning for the bounded, opt-in gfx906 pipeline preparation experiment.
// Bit T denotes the existing T-token graph; bit zero is never a valid shape.
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace strata::program {
constexpr int kPipelineShapeMaxT = 8;

inline bool pipeline_shape_opt_in(const char* value) {
    return value != nullptr && std::strcmp(value, "1") == 0;
}

inline bool pipeline_shape_gfx906(const char* arch, int warp_size) {
    return arch != nullptr && warp_size == 64 && std::strncmp(arch, "gfx906", 6) == 0 &&
           (arch[6] == '\0' || arch[6] == ':');
}

inline uint32_t pipeline_shape_range(int max_t) {
    if (max_t < 1 || max_t > kPipelineShapeMaxT) return 0;
    return (uint32_t(1) << (max_t + 1)) - 2u;
}

struct PipelineShapePlan {
    bool selective = false;   // false means use the unchanged eager capture_all API
    uint32_t mask[2] = {0, 0};
};

// Always include the configured decode range at the FIRST existing preparation
// boundary, even for a prompt-only request. This must not defer its cost to TG.
inline PipelineShapePlan pipeline_shape_plan(bool eligible, int spec, int mtp_max,
                                              int suffix_draft, const uint32_t prompt[2]) {
    PipelineShapePlan plan;
    const uint32_t full = pipeline_shape_range(spec);
    if (!eligible || full == 0 || mtp_max < 1 || mtp_max > spec || prompt == nullptr ||
        ((prompt[0] | prompt[1]) & ~full) != 0) return plan;
    const uint32_t decode = pipeline_shape_range(suffix_draft > 0 ? spec : mtp_max);
    plan.selective = true;
    plan.mask[0] = decode | prompt[0];
    plan.mask[1] = decode | prompt[1];
    return plan;
}

// The driver calls this on its original deterministic wins vector. Parity starts
// at zero for EACH read_windows_pl interval, as it does in the launch loop.
inline bool pipeline_shape_add_prompt(uint32_t prompt[2], std::size_t index, int tokens) {
    if (prompt == nullptr || tokens < 1 || tokens > kPipelineShapeMaxT) return false;
    prompt[index & 1u] |= uint32_t(1) << tokens;
    return true;
}
}  // namespace strata::program
