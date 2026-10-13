#include "strata/core/conversation_memory_budget.hpp"

#include <atomic>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <vector>

using strata::core::ConversationMemoryBudget;
using strata::core::ConversationMemoryInventory;
using strata::core::conversation_memory_add;
using strata::core::conversation_memory_multiply;
using Budget = ConversationMemoryBudget;
using Inventory = ConversationMemoryInventory;

#define CHECK(condition) do { if (!(condition)) { \
    std::cerr << __FILE__ << ':' << __LINE__ << ": " #condition " failed\n"; std::abort(); \
} } while (false)

static void check_invariant(const Budget& budget) {
    const auto s = budget.snapshot();
    size_t inventory = 0;
    CHECK(s.inventory.bytes(inventory));
    CHECK(s.owned == inventory);
    CHECK(s.owned <= s.limit);
    CHECK(s.reserved <= s.limit - s.owned);
    CHECK(s.total == s.owned + s.reserved);
    CHECK(s.high_water >= s.total && s.high_water <= s.limit);
}

static void exact_budget_and_zero() {
    Budget budget;
    CHECK(budget.snapshot().limit == UINT64_C(16777216) * 1024);
    auto whole = budget.reserve(Budget::default_limit_bytes);
    CHECK(whole);
    CHECK(budget.available() == 0);
    CHECK(!budget.reserve(1));
    auto zero = budget.reserve(0);
    CHECK(zero && zero.bytes() == 0);
    CHECK(budget.snapshot().outstanding == 2);
    zero.reset();
    whole.reset();
    CHECK(budget.available() == Budget::default_limit_bytes);
    check_invariant(budget);

    Budget disabled(0);
    CHECK(!disabled.reserve(1));
    auto nothing = disabled.reserve(0);
    CHECK(nothing);
    CHECK(nothing.commit({}));
    CHECK(!nothing);
}

static void arithmetic_and_overflow() {
    const size_t max = std::numeric_limits<size_t>::max();
    size_t out = 42;
    CHECK(!conversation_memory_add(max, 1, out) && out == 42);
    CHECK(!conversation_memory_multiply(max, 2, out) && out == 42);
    CHECK(conversation_memory_add(max - 1, 1, out) && out == max);
    CHECK(conversation_memory_multiply(max, 0, out) && out == 0);
    CHECK(conversation_memory_multiply(max, 1, out) && out == max);
    Inventory bad;
    bad.active = max;
    bad.parked = 1;
    CHECK(!bad.bytes(out));
    CHECK(bad.bytes() == max);
    Budget budget(max);
    CHECK(!budget.reconcile(bad));
    CHECK(budget.snapshot().breached);
    CHECK(budget.snapshot().last_failure == Budget::Failure::arithmetic_overflow);
    CHECK(!budget.reserve(0));
    CHECK(budget.reconcile({}));
    auto whole = budget.reserve(max);
    CHECK(whole && !budget.reserve(1));
    CHECK(whole.commit(Inventory{max}));
    CHECK(budget.snapshot().owned == max);
    check_invariant(budget);
}

static void raii_move_shrink_and_exceptions() {
    static_assert(!std::is_copy_constructible<Budget::Reservation>::value);
    static_assert(!std::is_copy_assignable<Budget::Reservation>::value);
    static_assert(std::is_nothrow_move_constructible<Budget::Reservation>::value);
    Budget budget(1000);
    {
        auto a = budget.reserve(400);
        auto b = budget.reserve(300);
        CHECK(a && b);
        b = std::move(a); // releases exactly b's 300; transfers a's 400
        CHECK(!a && b.bytes() == 400);
        CHECK(budget.snapshot().reserved == 400 && budget.snapshot().outstanding == 1);
        CHECK(!b.shrink(401));
        CHECK(b.shrink(200));
        Budget::Reservation c(std::move(b));
        CHECK(!b && c.bytes() == 200);
        auto* alias = &c;
        c = std::move(*alias); // self move cannot release the reservation
        CHECK(c && budget.snapshot().reserved == 200);
    }
    CHECK(budget.snapshot().reserved == 0 && budget.snapshot().outstanding == 0);
    try {
        auto capture = budget.reserve(700);
        CHECK(capture);
        // Simulate bad_alloc after one stage has completed. No publication.
        std::vector<unsigned char> first_stage(128);
        CHECK(!first_stage.empty());
        throw std::bad_alloc();
    } catch (const std::bad_alloc&) {}
    CHECK(budget.snapshot().reserved == 0);
    check_invariant(budget);
}

static void transfer_take_retain_split_merge() {
    Budget budget(1600);
    Inventory owners;
    owners.active = 600;
    owners.parked = 700;
    owners.retained = 100;
    owners.metadata = 20;
    CHECK(budget.reconcile(owners));
    const size_t initial = owners.bytes();

    // take() moves a parked image into a selected local; it does not free RAM.
    owners.parked -= 500;
    owners.selected += 500;
    CHECK(budget.reconcile(owners));
    CHECK(budget.snapshot().owned == initial);
    CHECK(budget.available() == 180);

    // Split makes directory/identity copies in addition to moved payload.
    auto split = budget.reserve(120);
    CHECK(split);
    owners.active -= 300;
    owners.inflight += 300;
    owners.temporary += 100;
    CHECK(split.commit(owners));
    CHECK(budget.snapshot().owned == initial + 100);
    CHECK(budget.snapshot().reserved == 0);
    // Move/merge does not double-count the same payload in both categories.
    owners.active += 300;
    owners.inflight -= 300;
    owners.temporary = 0;
    CHECK(budget.reconcile(owners));
    // Only retained KV remains after destroying the selected image's rest.
    owners.retained += 200;
    owners.selected = 0;
    CHECK(budget.reconcile(owners));
    CHECK(budget.snapshot().owned == initial - 300);
    check_invariant(budget);
}

static void replacement_and_all_stage_capture() {
    Budget budget(1000);
    Inventory owners;
    owners.active = 600;
    CHECK(budget.reconcile(owners));
    // A 600-byte replacement cannot be justified by its final net-zero size.
    CHECK(!budget.reserve(600));
    CHECK(budget.snapshot().last_failure == Budget::Failure::no_room);
    CHECK(!budget.snapshot().breached);
    CHECK(budget.snapshot().owned == 600);
    // Reserve every stage and temporary metadata before stage zero begins.
    auto complete = budget.reserve(350); // 100 + 200 + 50 transient
    CHECK(complete);
    CHECK(!budget.reserve(51));
    owners.active += 300;
    CHECK(complete.commit(owners));
    CHECK(budget.snapshot().owned == 900);
    CHECK(budget.snapshot().high_water == 950);
    // Old active state can be released only once replacement exists.
    owners.active -= 600;
    CHECK(budget.reconcile(owners));
    CHECK(budget.available() == 700);
    check_invariant(budget);
}

static void underestimated_capture_fails_closed() {
    Budget budget(1000);
    Inventory owners{100};
    CHECK(budget.reconcile(owners));
    auto capture = budget.reserve(200);
    Inventory actual = owners;
    actual.inflight = 201;
    CHECK(!capture.commit(actual)); // actual capacity exceeded reservation
    CHECK(capture); // caller must roll back before releasing the token
    CHECK(budget.snapshot().breached);
    CHECK(budget.snapshot().last_failure == Budget::Failure::reservation_underestimated);
    CHECK(budget.snapshot().owned == 100 && budget.snapshot().reserved == 200);
    CHECK(budget.available() == 0 && budget.parked_headroom(1000) == 0);
    CHECK(!budget.reserve(1));
    // Destroy unpublished capture, release reservation, re-audit live owners.
    capture.reset();
    CHECK(!budget.reserve(1));
    CHECK(budget.reconcile(owners));
    CHECK(!budget.snapshot().breached && budget.available() == 900);
    check_invariant(budget);
}

static void concurrent_reservations_and_atomic_commit() {
    Budget budget(1000);
    Inventory owners{200};
    CHECK(budget.reconcile(owners));
    auto first = budget.reserve(300);
    auto second = budget.reserve(400);
    CHECK(first && second);
    owners.inflight = 280;
    CHECK(first.commit(owners));
    CHECK(budget.snapshot().owned == 480 && budget.snapshot().reserved == 400);
    owners.inflight += 390;
    CHECK(second.commit(owners));
    CHECK(budget.snapshot().owned == 870 && budget.snapshot().reserved == 0);
    CHECK(budget.snapshot().high_water == 900);
    CHECK(budget.reconcile({}));

    std::atomic<unsigned> ready{0};
    std::atomic<bool> release{false};
    std::vector<std::thread> workers;
    for (unsigned k = 0; k < 8; ++k) {
        workers.emplace_back([&] {
            std::vector<Budget::Reservation> tickets;
            for (;;) {
                auto ticket = budget.reserve(100);
                if (!ticket) break;
                tickets.push_back(std::move(ticket));
                check_invariant(budget);
                std::this_thread::yield();
            }
            ++ready;
            while (!release.load()) std::this_thread::yield();
        });
    }
    while (ready.load() != 8) std::this_thread::yield();
    CHECK(budget.snapshot().reserved == 1000);
    CHECK(budget.snapshot().outstanding == 10);
    CHECK(budget.snapshot().high_water == 1000);
    release = true;
    for (auto& worker : workers) worker.join();
    CHECK(budget.snapshot().reserved == 0 && budget.snapshot().outstanding == 0);
    check_invariant(budget);
}

static void parked_subordinate_cap_and_invalid_audit() {
    Budget budget(1600);
    Inventory owners;
    owners.active = 700;
    owners.parked = 500;
    owners.retained = 100;
    owners.selected = 50;
    owners.metadata = 10;
    CHECK(budget.reconcile(owners));
    CHECK(budget.parked_headroom(1200) == 840);
    CHECK(budget.parked_headroom(500) == 500);
    auto stage = budget.reserve(200);
    CHECK(stage);
    CHECK(budget.parked_headroom(1200) == 640);
    Inventory impossible = owners;
    impossible.temporary = 41;
    CHECK(!budget.reconcile(impossible));
    CHECK(budget.snapshot().breached);
    CHECK(budget.snapshot().total == 1560);
    CHECK(budget.snapshot().last_failure == Budget::Failure::inventory_over_budget);
    stage.reset();
    CHECK(budget.reconcile(owners));
    CHECK(budget.available() == 240);
    check_invariant(budget);
}

int main() {
    exact_budget_and_zero();
    arithmetic_and_overflow();
    raii_move_shrink_and_exceptions();
    transfer_take_retain_split_merge();
    replacement_and_all_stage_capture();
    underestimated_capture_fails_closed();
    concurrent_reservations_and_atomic_commit();
    parked_subordinate_cap_and_invalid_audit();
    std::cout << "conversation_memory_budget: 8 CPU test groups passed\n";
}
