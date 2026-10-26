#pragma once
#include <cstdint>

namespace strata::program::pending_prefix {
// Host-only planning. No device code or change to verification/commit arithmetic.
inline bool requested(const char* value) {
    return value && value[0] == '1' && value[1] == 0;
}
inline bool checked_limit(int64_t n, int64_t cap, int64_t context, int64_t& limit) {
    limit = 0;
    // Same eight-token reserve as the native GEN context admission, without signed addition overflow.
    if (context < 8 || n < 1 || n > context - 8 || cap < 1 || cap > context - 8 - n)
        return false;
    limit = (n - 1) + cap;
    return true;
}
inline bool eligible(bool wanted, bool text, int batch, int windows, int max_t,
                     int merged, int suffix, int lookup, bool coupled, int history) {
    return wanted && text && batch == 0 && windows == 2 && max_t >= 1 && max_t <= 2
           && merged == 0 && suffix == 0 && lookup == 0 && !coupled && history == 0;
}
inline int width(int64_t limit, int64_t position, int proposed) {
    if (position < 0 || position >= limit || proposed < 1 || proposed > 2) return 0;
    const int64_t remaining = limit - position;
    return remaining < proposed ? static_cast<int>(remaining) : proposed;
}
} // namespace strata::program::pending_prefix
