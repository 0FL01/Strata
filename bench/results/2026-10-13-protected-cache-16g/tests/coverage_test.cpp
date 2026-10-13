#include "coverage.hpp"
#ifdef COVERAGE_WITH_BUDGET_TESTS
#include <strata/core/conversation_memory_budget.hpp>
#endif

#include <algorithm>
#include <cassert>
#include <iostream>
#include <limits>
#include <random>
#include <vector>

namespace cov = strata::program::coverage;
struct Checkpoint {
    int64_t length, target;
    uint64_t stamp;
};

// A test-only bank. Production owns coherent payloads and global admission;
// this harness deliberately models only integer positions, not GPU state.
struct Bank {
    cov::State state;
    std::vector<Checkpoint> points;
    uint64_t clock = 0;
    size_t captures = 0;
    explicit Bank(int64_t step = 16384) : state(step) {}

    void arrays(std::vector<int64_t>& lengths, std::vector<int64_t>& targets,
                std::vector<uint64_t>& stamps) const {
        for (const auto& p : points) {
            lengths.push_back(p.length); targets.push_back(p.target);
            stamps.push_back(p.stamp);
        }
    }
    void compact() {
        for (;;) {
            std::vector<int64_t> l, t; std::vector<uint64_t> u;
            arrays(l, t, u);
            const auto victim = cov::eviction_victim(l.data(), u.data(), t.data(), l.size());
            if (!victim) return;
            points.erase(points.begin() + *victim);
        }
    }
    bool save(int64_t length, bool budget_admitted = true, bool coherent = true) {
        if (!budget_admitted || !coherent) {
            if (state.due(length)) state.failed(length, !budget_admitted ?
                cov::HoleReason::budget : cov::HoleReason::incomplete_snapshot);
            return false;
        }
        auto it = std::find_if(points.begin(), points.end(), [=](auto p) {
            return p.length == length;
        });
        const auto target = state.saved(length);
        if (it == points.end()) { points.push_back({length, target, ++clock}); ++captures; }
        else { if (it->target == 0) it->target = target; it->stamp = ++clock; }
        compact();
        return true;
    }
    void opportunity(int64_t length, bool recent = false) {
        if (state.due(length) || recent || points.empty()) save(length);
    }
    int64_t best(int64_t lcp) const {
        int64_t result = 0;
        for (auto p : points) if (p.length <= lcp) result = std::max(result, p.length);
        return result;
    }
    int64_t branch(int64_t lcp, bool trusted = true) {
        points.erase(std::remove_if(points.begin(), points.end(), [=](auto p) {
            return p.length > lcp;
        }), points.end());
        auto resume = best(lcp);
        std::vector<int64_t> l, t; std::vector<uint64_t> u; arrays(l, t, u);
        state.rebuild(l.data(), t.data(), l.size(), resume, trusted);
        return resume;
    }
    size_t anchors() const {
        return std::count_if(points.begin(), points.end(), [](auto p) { return p.target != 0; });
    }
};

void test_recorded_req22() {
    const int64_t creation[] = {
        10674,18866,35250,51634,68018,84402,100786,117170,128556,
        130649,131843,132390,133472,135692,136089,136224,136708,
        137671,138898,139699,140588,141351,142059,142574,144744,
        145209,145658,146409,147644
    };
    const int64_t expected[] = {18866,35250,51634,68018,84402,100786,117170,131843,147644};
    Bank bank;
    for (auto length : creation) assert(bank.save(length));
    std::vector<int64_t> anchors;
    for (auto point : bank.points) if (point.target) anchors.push_back(point.length);
    assert(anchors == std::vector<int64_t>(std::begin(expected), std::end(expected)));
    assert(bank.best(117131) == 100786);
    assert(134088 - bank.best(117131) == 33302);
    assert(bank.points.size() == 12); // root + nine anchors + two ordinary recents
    assert(bank.state.next_target == 163840);
    std::cout << "recorded_req22: resume=100786 total_read=33302 anchors=9 retained=12\n";
}

void test_long_and_short_turns() {
    size_t exhaustive = 0;
    std::mt19937 rng(20261013);
    for (int64_t maximum_gap : {64, 1024, 4096, 32768}) {
        Bank bank;
        int64_t pos = 0;
        while (pos < 262144) {
            pos = std::min<int64_t>(262144, pos + 1 + rng() % maximum_gap);
            bank.opportunity(pos, rng() % 4 == 0);
        }
        assert(!bank.state.has_hole());
        assert(bank.state.next_target == 0);
        assert(bank.points.size() <= 19);
        for (int64_t lcp = 0; lcp <= 262144; ++lcp) {
            assert(lcp - bank.best(lcp) < 16384 + maximum_gap);
            ++exhaustive;
        }
        // Random branches, including cancellation exactly at an accepted endpoint.
        for (int trial = 0; trial < 400; ++trial) {
            int64_t lcp = rng() % 262145;
            pos = bank.branch(lcp);
            assert(!bank.state.has_hole());
            while (pos < 262144) {
                pos = std::min<int64_t>(262144, pos + 1 + rng() % maximum_gap);
                bank.opportunity(pos, rng() % 8 == 0);
            }
            assert(!bank.state.has_hole() && bank.state.next_target == 0);
            assert(bank.points.size() <= 19);
        }
    }
    Bank tiny;
    size_t turns = 0;
    for (int64_t pos = 1; pos <= 262144; pos += 31) {
        // State deliberately persists across requests individually far below B.
        tiny.opportunity(pos, true);
        ++turns;
    }
    tiny.opportunity(262144, true);
    assert(tiny.anchors() == 16 && tiny.points.size() <= 19);
    assert(tiny.state.next_target == 0 && !tiny.state.has_hole());
    std::cout << "coverage: " << exhaustive << " exhaustive LCP checks, 1600 branch/refill cases, "
              << turns << " short turns; context=262144\n";
}

void test_roles_and_no_victim() {
    const int64_t lengths[] = {500, 100, 400, 300, 200, 600, 700}; // deliberately unsorted
    const int64_t targets[] = {0, 0, 384, 0, 0, 512, 0};
    const uint64_t stamps[] = {100, 1, 102, 99, 2, 103, 98};
    const bool pins[] = {false, false, false, false, true, false, false};
    auto victim = cov::eviction_victim(lengths, stamps, targets, 7, pins);
    assert(victim && *victim == 6); // root index1; two ordinary heads index0/index3
    const int64_t protected_lengths[] = {100, 200, 300, 400, 500};
    const int64_t protected_targets[] = {0, 128, 256, 0, 0};
    const uint64_t protected_stamps[] = {1, 2, 3, 4, 5};
    assert(!cov::eviction_victim(protected_lengths, protected_stamps, protected_targets, 5));
    assert(!cov::eviction_victim(nullptr, nullptr, nullptr, 0));
    const bool all_pins[] = {true,true,true,true,true,true,true};
    assert(!cov::eviction_victim(lengths, stamps, targets, 7, all_pins));
    // Promotion protects the old tail; ordinary recent allowance stays at two.
    Bank b(128);
    b.save(100); b.save(129); b.save(150); b.save(170);
    assert(b.points.size() == 4);
    b.save(257);
    assert(b.points.size() == 5 && b.anchors() == 2);
    b.save(270); b.save(280);
    assert(b.points.size() == 5 && b.anchors() == 2);
    for (auto p : b.points) assert(p.length != 150 && p.length != 170);
    std::cout << "roles: root/coverage/recent2/user-pin isolation and no-victim saturation passed\n";
}

void test_failure_restore_and_cancel() {
    Bank b;
    b.save(1000);
    const auto before = b.points;
    assert(!b.save(16390, false));
    assert(b.points.size() == before.size());
    assert(b.state.next_target == 16384 && b.state.hole == cov::HoleReason::budget);
    b.save(17000);
    assert(b.state.next_target == 32768 && b.state.has_hole());
    // Parking copies metadata, including degraded coverage, with the owned bank.
    Bank parked = b;
    parked.branch(17000);
    assert(parked.state.hole == cov::HoleReason::budget);
    parked.branch(1000);
    assert(!parked.state.has_hole() && parked.state.next_target == 16384);
    assert(!parked.save(16390, true, false));
    assert(parked.state.next_target == 16384);
    assert(parked.state.hole == cov::HoleReason::incomplete_snapshot);
    // Cancel before commit is NOT a capture opportunity and changes nothing.
    auto pending = parked.state.next_target;
    assert(parked.state.next_target == pending);
    // Commit success before EOS/cancel does make the endpoint eligible; sticky
    // hole remains until actual rewind/replay repairs the affected interval.
    parked.branch(1000);
    parked.save(16390);
    assert(!parked.state.has_hole());
    assert(parked.state.next_target == 32768);
    auto duplicate_count = parked.captures;
    parked.save(16390);
    assert(parked.captures == duplicate_count);
    // Legacy or incomplete disk restore must never manufacture older anchors.
    cov::State legacy;
    const int64_t lengths[] = {1000, 100000};
    const int64_t no_targets[] = {0, 0};
    assert(!legacy.rebuild(lengths, no_targets, 2, 100000, false));
    assert(legacy.hole == cov::HoleReason::legacy_restore && legacy.next_target == 16384);
    assert(legacy.saved(110000) == 16384 && legacy.has_hole());
    assert(legacy.rebuild(nullptr, nullptr, 0, 0, true));
    assert(legacy.next_target == 16384 && !legacy.has_hole());
    // A missing intermediate anchor is a hole even with trusted provenance.
    cov::State missing;
    const int64_t l[] = {17000, 50000}; const int64_t t[] = {16384, 49152};
    assert(!missing.rebuild(l, t, 2, 50000, true));
    assert(missing.next_target == 32768 && missing.hole == cov::HoleReason::missing_anchor);
    std::cout << "failures: budget/incomplete preserve timer, sticky restore, branch repair, cancellation passed\n";
}

void test_large_opportunity_and_extremes() {
    cov::State state;
    assert(state.saved(50000) == 16384); // one actual checkpoint represents targets 16/32/48K
    assert(state.next_target == 65536);
    const int64_t l[] = {50000}; const int64_t t[] = {16384};
    assert(state.rebuild(l, t, 1, 50000, true) && state.next_target == 65536);
    cov::State huge(std::numeric_limits<int64_t>::max() - 1,
                    std::numeric_limits<int64_t>::max());
    assert(huge.saved(std::numeric_limits<int64_t>::max()) ==
           std::numeric_limits<int64_t>::max() - 1);
    assert(huge.next_target == 0);
    cov::State zero(0); assert(zero.has_hole() && !zero.due(100));
    cov::State bad;
    const int64_t invalid[] = {0};
    assert(!bad.rebuild(invalid, invalid, 1, 100, true));
    assert(bad.hole == cov::HoleReason::invalid_metadata);
    cov::State malformed;
    const int64_t bad_target[] = {123};
    assert(!malformed.rebuild(l, bad_target, 1, 50000, true));
    std::cout << "edge cases: multiple crossed targets, overflow endpoints, malformed metadata passed\n";
}

#ifdef COVERAGE_WITH_BUDGET_TESTS
void test_global_budget_admission() {
    using Budget = strata::core::ConversationMemoryBudget;
    using Inventory = strata::core::ConversationMemoryInventory;
    constexpr size_t gib = size_t{1024} * 1024 * 1024;
    constexpr size_t payload_fixed = 118431992; // historical model fit, not universal
    auto bytes_at = [](int64_t length) { return payload_fixed + 8 * size_t(length); };
    auto active_bytes = [&](const Bank& b) {
        size_t total = 0; for (auto p : b.points) total += bytes_at(p.length); return total;
    };
    Budget budget;
    Inventory inventory;
    inventory.parked = 12 * gib;
    inventory.retained = gib;
    inventory.metadata = 4096;
    assert(budget.reconcile(inventory));
    Bank bank;
    auto publish = [&](int64_t position) {
        // Admission occurs BEFORE hypothetical snapshot allocation. Old bank
        // remains charged and valid during the candidate's lifetime.
        auto ticket = budget.reserve(bytes_at(position));
        if (!ticket) { bank.state.failed(position, cov::HoleReason::budget); return false; }
        Bank candidate = bank; // metadata-only model, NOT an actual payload copy
        candidate.save(position);
        auto proposed = inventory;
        proposed.active = active_bytes(candidate);
        if (!ticket.commit(proposed)) {
            bank.state.failed(position, cov::HoleReason::budget);
            return false;
        }
        bank = std::move(candidate);
        inventory = proposed;
        assert(budget.snapshot().total <= 16 * gib);
        return true;
    };
    assert(publish(1000));
    for (int64_t p = 16384; p <= 262144; p += 16384) {
        assert(publish(p));
        if (p < 262144) { assert(publish(p + 1)); assert(publish(p + 2)); }
    }
    assert(bank.anchors() == 16 && bank.points.size() == 19);
    assert(!bank.state.has_hole());
    assert(budget.snapshot().high_water <= 16 * gib);
    // Leave one byte less than required peak. Required capture is rejected,
    // without clearing existing anchors, advancing a timer, or evicting a pin.
    bank.branch(245760);
    inventory.active = active_bytes(bank);
    inventory.parked = 16 * gib - inventory.active - inventory.retained -
        inventory.metadata - bytes_at(262144) + 1;
    assert(budget.reconcile(inventory));
    const auto count = bank.points.size();
    const auto anchors = bank.anchors();
    const auto pending = bank.state.next_target;
    assert(!publish(262144));
    assert(bank.points.size() == count && bank.anchors() == anchors);
    assert(bank.state.next_target == pending && bank.state.hole == cov::HoleReason::budget);
    assert(budget.snapshot().reserved == 0 && !budget.snapshot().breached);
    std::cout << "global budget: full 256K bank plus 13 GiB other owners fits 16 GiB; "
                 "one-byte-short candidate rejected without protected loss\n";
}
#endif

int main() {
    test_recorded_req22(); test_long_and_short_turns(); test_roles_and_no_victim();
    test_failure_restore_and_cancel(); test_large_opportunity_and_extremes();
#ifdef COVERAGE_WITH_BUDGET_TESTS
    test_global_budget_admission();
#endif
    std::cout << "PASS: host coverage policy only; no GPU/coherent-state/latency claim\n";
}
