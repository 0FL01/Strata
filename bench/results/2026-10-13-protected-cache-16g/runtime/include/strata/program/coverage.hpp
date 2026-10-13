// Host-only, opt-in coverage metadata. No tensor copies, allocations, user-pin
// changes, global-budget ownership, or modifications of evaluation geometry.
#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace strata::program::coverage {

inline constexpr int64_t default_spacing = 16384;
inline constexpr int64_t default_max_context = 262144;

enum class HoleReason : uint8_t {
    none, budget, incomplete_snapshot, transfer_failed, unsupported_mode,
    legacy_restore, missing_anchor, opportunity_gap, invalid_metadata,
    no_eligible_victim
};

inline const char* reason_name(HoleReason reason) noexcept {
    switch (reason) {
    case HoleReason::none: return "none";
    case HoleReason::budget: return "budget";
    case HoleReason::incomplete_snapshot: return "incomplete_snapshot";
    case HoleReason::transfer_failed: return "transfer_failed";
    case HoleReason::unsupported_mode: return "unsupported_mode";
    case HoleReason::legacy_restore: return "legacy_restore";
    case HoleReason::missing_anchor: return "missing_anchor";
    case HoleReason::opportunity_gap: return "opportunity_gap";
    case HoleReason::invalid_metadata: return "invalid_metadata";
    case HoleReason::no_eligible_victim: return "no_eligible_victim";
    }
    return "invalid_reason";
}

// Move/copy this value along with its checkpoint bank when parking/restoring.
// A disk format that does not carry this value must reload as untrusted history.
// "No hole" certifies metadata history only, NOT snapshot correctness or an
// opportunity-gap bound; the caller must verify both before advertising a bound.
struct State {
    int64_t spacing = default_spacing;
    int64_t max_context = default_max_context;
    int64_t next_target = default_spacing;  // 0 means all in-context targets covered
    int64_t frontier = 0;
    int64_t hole_target = 0;                // earliest affected absolute threshold
    HoleReason hole = HoleReason::none;

    explicit State(int64_t step = default_spacing,
                   int64_t maximum = default_max_context) noexcept
        : spacing(step), max_context(maximum),
          next_target(step > 0 && maximum >= step ? step : 0) {
        if (step <= 0 || maximum <= 0) {
            hole = HoleReason::invalid_metadata;
        }
    }

    bool valid_config() const noexcept { return spacing > 0 && max_context > 0; }
    bool has_hole() const noexcept { return hole != HoleReason::none; }
    bool due(int64_t length) const noexcept {
        return valid_config() && next_target > 0 && length >= next_target &&
               length <= max_context;
    }

    // Does not overflow at INT64_MAX and does not invent a target past context.
    int64_t target_after(int64_t length) const noexcept {
        if (!valid_config() || length < 0 || length > max_context) return 0;
        const int64_t base = (length / spacing) * spacing;
        return max_context - base < spacing ? 0 : base + spacing;
    }

    void failed(int64_t length, HoleReason reason) noexcept {
        if (reason == HoleReason::none) return;
        const int64_t target = next_target > 0 ? next_target :
            (valid_config() && length > 0 ? (length / spacing) * spacing : 0);
        mark_hole(target, reason);
    }

    // Call ONLY after complete exact-state capture/promotion AND global memory
    // admission have succeeded. Store the returned value in coverage_target.
    // A single endpoint can satisfy multiple targets when opportunity gap > B:
    // it represents every absolute target in [returned, floor(length/B)*B].
    // Its real saved length remains length, never the nominal target.
    int64_t saved(int64_t length) noexcept {
        if (!valid_config() || length < 0 || length > max_context) {
            failed(length, HoleReason::invalid_metadata);
            return 0;
        }
        if (length > frontier) frontier = length;
        if (!due(length)) return 0;
        const int64_t target = next_target;
        next_target = target_after(length);
        // A later successful snapshot cannot retroactively repair a missed one.
        return target;
    }

    // Rebuild after prefix/identity pruning, before continuing a restored bank.
    // Arrays may be unsorted. They must describe ONLY compatible, coherent states
    // at or before evaluated_through. A coverage target of zero is an ordinary
    // root/recent/user-pin snapshot. It is not silently promoted by this function.
    // trusted_history means history originated at zero and its State was retained;
    // passing true does not erase a retained hole. Legacy restores should pass false.
    // Returns metadata coverage availability, not numerical-state validation.
    bool rebuild(const int64_t* lengths, const int64_t* targets, size_t n,
                 int64_t evaluated_through, bool trusted_history) noexcept {
        const HoleReason previous_hole = hole;
        const int64_t previous_target = hole_target;
        hole = HoleReason::none;
        hole_target = 0;
        frontier = evaluated_through;
        next_target = valid_config() && spacing <= max_context ? spacing : 0;
        if (!valid_config() || evaluated_through < 0 ||
            evaluated_through > max_context || (n != 0 && (!lengths || !targets))) {
            mark_hole(0, HoleReason::invalid_metadata);
            return false;
        }
        for (size_t i = 0; i < n; ++i) {
            if (lengths[i] <= 0 || lengths[i] > evaluated_through ||
                targets[i] < 0 || targets[i] > lengths[i] ||
                (targets[i] != 0 && targets[i] % spacing != 0)) {
                mark_hole(0, HoleReason::invalid_metadata);
                return false;
            }
        }
        // Union all explicitly represented target ranges. No synthetic target
        // is filled by a recent checkpoint or by an unrelated later anchor.
        bool advanced = true;
        while (next_target != 0 && advanced) {
            advanced = false;
            for (size_t i = 0; i < n; ++i) {
                if (targets[i] == 0 || targets[i] > next_target ||
                    lengths[i] < next_target) continue;
                next_target = target_after(lengths[i]);
                advanced = true;
                if (next_target == 0) break;
            }
        }
        // Rewinding strictly before the affected threshold permits genuine
        // replay to repair that failure. Otherwise retain it across park/restore.
        if (previous_hole != HoleReason::none &&
            ((previous_target == 0 && evaluated_through > 0) ||
             (previous_target > 0 && previous_target <= evaluated_through))) {
            mark_hole(previous_target, previous_hole);
        }
        if (!trusted_history && evaluated_through > 0) {
            mark_hole(0, HoleReason::legacy_restore);
        }
        if (next_target != 0 && next_target <= evaluated_through) {
            mark_hole(next_target, HoleReason::missing_anchor);
        }
        return !has_hole();
    }

private:
    void mark_hole(int64_t target, HoleReason reason) noexcept {
        if (!has_hole() || target < hole_target) {
            hole_target = target;
            hole = reason;
        }
    }
};

// Return no victim when all snapshots are protected. NEVER fall back to the old
// pin-victim rule. Root is minimum length, independent of container order. Recent
// points are the two highest used/capture stamps among otherwise unprotected
// snapshots (length then index break ties). User pins remain independent flags.
// A nonzero coverage tag is conservatively protected even if metadata is invalid.
inline std::optional<size_t> eviction_victim(
    const int64_t* lengths, const uint64_t* stamps, const int64_t* targets,
    size_t n, const bool* user_pins = nullptr, size_t recent_count = 2,
    const bool* tails = nullptr) noexcept {
    if (n == 0 || !lengths || !stamps || !targets) return std::nullopt;
    size_t root = 0;
    for (size_t i = 1; i < n; ++i)
        if (lengths[i] < lengths[root]) root = i;
    auto newer = [&](size_t a, size_t b) {
        return stamps[a] > stamps[b] ||
            (stamps[a] == stamps[b] && (lengths[a] > lengths[b] ||
              (lengths[a] == lengths[b] && a > b)));
    };
    auto fixed_role = [&](size_t i) {
        return i == root || targets[i] != 0 || (user_pins && user_pins[i]);
    };
    auto protected_item = [&](size_t i) {
        if (fixed_role(i)) return true;
        size_t newer_count = 0;
        for (size_t j = 0; j < n && newer_count < recent_count; ++j)
            if (!fixed_role(j) && newer(j, i)) ++newer_count;
        return newer_count < recent_count;
    };
    std::optional<size_t> result;
    for (size_t i = 0; i < n; ++i) {
        if (protected_item(i)) continue;
        if (!result || (tails && tails[i] && !tails[*result]) ||
            ((!tails || tails[i] == tails[*result]) &&
             (stamps[i] < stamps[*result] ||
              (stamps[i] == stamps[*result] && lengths[i] < lengths[*result])))) {
            result = i;
        }
    }
    return result;
}

}  // namespace strata::program::coverage
