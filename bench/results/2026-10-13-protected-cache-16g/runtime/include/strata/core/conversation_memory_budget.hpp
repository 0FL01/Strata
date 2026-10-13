// Host-cache ownership admission, independent of the physical-RAM floor.
// This bounds accounted capacities + pre-allocation reservations, NOT RSS.
#pragma once

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include <mutex>
#include <utility>

namespace strata::core {

inline bool conversation_memory_add(size_t a, size_t b, size_t& out) noexcept {
    if (b > std::numeric_limits<size_t>::max() - a) return false;
    out = a + b;
    return true;
}

inline bool conversation_memory_multiply(size_t a, size_t b, size_t& out) noexcept {
    if (a && b > std::numeric_limits<size_t>::max() / a) return false;
    out = a * b;
    return true;
}

// Categories are mutually exclusive OWNERS, not references to the same data.
// parked excludes retained KV; selected is a detached take() result; inflight
// contains committed stage parts. A part covered by a live Reservation must
// not appear here until that reservation is committed. Charge spare vector
// capacity and directory capacity, including directories whose size is zero.
struct ConversationMemoryInventory {
    size_t active = 0;
    size_t parked = 0;
    size_t retained = 0;
    size_t selected = 0;
    size_t inflight = 0;
    size_t temporary = 0;
    size_t metadata = 0;

    bool bytes(size_t& out) const noexcept {
        size_t total = 0;
        for (size_t n : {active, parked, retained, selected, inflight, temporary, metadata})
            if (!conversation_memory_add(total, n, total)) return false;
        out = total;
        return true;
    }

    size_t bytes() const noexcept {
        size_t out = 0;
        return bytes(out) ? out : std::numeric_limits<size_t>::max();
    }
};

class ConversationMemoryBudget {
public:
    // 16 GiB = 16,777,216 KiB. This is separate from a subordinate parked cap.
    static constexpr uint64_t default_limit_bytes = UINT64_C(16) * 1024 * 1024 * 1024;

    enum class Failure {
        none,
        no_room,
        arithmetic_overflow,
        inventory_over_budget,
        reservation_underestimated,
        unreconciled_inventory
    };

    struct Snapshot {
        ConversationMemoryInventory inventory;
        size_t limit = 0, owned = 0, reserved = 0, total = 0, high_water = 0;
        size_t outstanding = 0;
        bool breached = false;
        Failure last_failure = Failure::none;
    };

    class Reservation {
    public:
        Reservation() noexcept = default;
        Reservation(const Reservation&) = delete;
        Reservation& operator=(const Reservation&) = delete;
        Reservation(Reservation&& other) noexcept
            : owner_(std::exchange(other.owner_, nullptr)), bytes_(std::exchange(other.bytes_, 0)) {}
        Reservation& operator=(Reservation&& other) noexcept {
            if (this != &other) {
                reset();
                owner_ = std::exchange(other.owner_, nullptr);
                bytes_ = std::exchange(other.bytes_, 0);
            }
            return *this;
        }
        ~Reservation() { reset(); }

        explicit operator bool() const noexcept { return owner_ != nullptr; }
        size_t bytes() const noexcept { return bytes_; }

        // Call only after uncommitted allocations are destroyed, or after the
        // same allocation has been transferred to another accounting owner.
        void reset() noexcept {
            if (owner_) {
                owner_->release(bytes_);
                owner_ = nullptr;
                bytes_ = 0;
            }
        }

        // Atomically replace this reservation by a complete owned inventory.
        // Growth above the reservation is rejected even if spare room exists.
        // This is a final-capacity audit, not a peak measurement: simultaneous
        // frees can hide temporary growth. The caller must separately bound
        // every pre-allocation peak (old+new directories, copies, all stages).
        // Failure leaves the token intact for destruction/rollback; no partially
        // built multi-stage checkpoint may be published on failure.
        bool commit(const ConversationMemoryInventory& inventory) noexcept {
            if (!owner_ || !owner_->commit(*this, inventory)) return false;
            owner_ = nullptr;
            bytes_ = 0;
            return true;
        }

        // Return excess reservation only after the corresponding temporary
        // allocation is gone or its remaining maximum has been established.
        bool shrink(size_t bytes) noexcept {
            if (!owner_ || bytes > bytes_) return false;
            owner_->shrink(bytes_ - bytes);
            bytes_ = bytes;
            return true;
        }

    private:
        friend class ConversationMemoryBudget;
        Reservation(ConversationMemoryBudget* owner, size_t bytes) noexcept : owner_(owner), bytes_(bytes) {}
        ConversationMemoryBudget* owner_ = nullptr;
        size_t bytes_ = 0;
    };

    explicit ConversationMemoryBudget(size_t limit = static_cast<size_t>(default_limit_bytes)) noexcept
        : limit_(limit) {
        static_assert(sizeof(size_t) >= sizeof(uint64_t), "host-cache budget requires 64-bit size_t");
    }
    ConversationMemoryBudget(const ConversationMemoryBudget&) = delete;
    ConversationMemoryBudget& operator=(const ConversationMemoryBudget&) = delete;
    ~ConversationMemoryBudget() { assert(outstanding_ == 0 && "budget must outlive its reservations"); }

    // Rebuild the inventory at serialized ownership boundaries, including
    // after release/move/eviction and initially before enabling admission.
    // This is an audit, never permission to allocate before reserve(). A failed
    // audit preserves the last valid ledger, marks it unreliable, and blocks
    // admission until rollback is followed by a successful reconciliation.
    bool reconcile(const ConversationMemoryInventory& inventory) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        size_t n = 0;
        if (!inventory.bytes(n)) return breach_locked(Failure::arithmetic_overflow);
        if (n > limit_ || reserved_ > limit_ - n) return breach_locked(Failure::inventory_over_budget);
        inventory_ = inventory;
        owned_ = n;
        breached_ = false;
        failure_ = Failure::none;
        observe_locked();
        return true;
    }

    // Reserve ALL additional peak capacity before the first allocation. Keep
    // old owners charged throughout replacement, checkpoint splitting, restore,
    // and deep copies. Concurrent captures each need their own reservation.
    Reservation reserve(size_t additional_peak) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        if (breached_) {
            failure_ = Failure::unreconciled_inventory;
            return {};
        }
        if (additional_peak > limit_ - owned_ - reserved_) {
            failure_ = Failure::no_room;
            return {};
        }
        if (outstanding_ == std::numeric_limits<size_t>::max()) {
            failure_ = Failure::arithmetic_overflow;
            return {};
        }
        reserved_ += additional_peak;
        ++outstanding_;
        failure_ = Failure::none;
        observe_locked();
        return Reservation(this, additional_peak);
    }

    Snapshot snapshot() const noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        assert_invariant_locked();
        return {inventory_, limit_, owned_, reserved_, owned_ + reserved_, high_water_,
                outstanding_, breached_, failure_};
    }

    size_t available() const noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        return breached_ ? 0 : limit_ - owned_ - reserved_;
    }

    // Current TOTAL allowance for parked + retained owners, not additional
    // bytes. Selected/inflight/active/reserved ownership reduces it. Caller
    // must still reserve before allocation; this number is only a snapshot.
    size_t parked_headroom(size_t subordinate_cap) const noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        if (breached_) return 0;
        const size_t parked = inventory_.parked + inventory_.retained; // part of checked owned_
        const size_t nonparked = owned_ - parked;
        return std::min(subordinate_cap, limit_ - nonparked - reserved_);
    }

private:
    bool breach_locked(Failure reason) noexcept {
        breached_ = true;
        failure_ = reason;
        assert_invariant_locked();
        return false;
    }

    bool commit(Reservation& reservation, const ConversationMemoryInventory& inventory) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        assert(reservation.owner_ == this && reservation.bytes_ <= reserved_ && outstanding_ != 0);
        if (breached_) {
            failure_ = Failure::unreconciled_inventory;
            return false;
        }
        size_t n = 0;
        if (!inventory.bytes(n)) return breach_locked(Failure::arithmetic_overflow);
        if (n > owned_ && n - owned_ > reservation.bytes_)
            return breach_locked(Failure::reservation_underestimated);
        const size_t other_reserved = reserved_ - reservation.bytes_;
        if (n > limit_ || other_reserved > limit_ - n)
            return breach_locked(Failure::inventory_over_budget);
        inventory_ = inventory;
        owned_ = n;
        reserved_ = other_reserved;
        --outstanding_;
        failure_ = Failure::none;
        observe_locked();
        return true;
    }

    void release(size_t bytes) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        assert(bytes <= reserved_ && outstanding_ != 0);
        reserved_ -= bytes;
        --outstanding_;
        assert_invariant_locked();
    }

    void shrink(size_t bytes) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);
        assert(bytes <= reserved_);
        reserved_ -= bytes;
        assert_invariant_locked();
    }

    void observe_locked() noexcept {
        assert_invariant_locked();
        high_water_ = std::max(high_water_, owned_ + reserved_);
    }
    void assert_invariant_locked() const noexcept {
        assert(owned_ <= limit_ && reserved_ <= limit_ - owned_);
    }

    mutable std::mutex mutex_;
    const size_t limit_;
    ConversationMemoryInventory inventory_;
    size_t owned_ = 0, reserved_ = 0, high_water_ = 0, outstanding_ = 0;
    bool breached_ = false;
    Failure failure_ = Failure::none;
};

} // namespace strata::core
