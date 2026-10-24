#pragma once
// Host-only, default-OFF research plan. No allocation policy or device code.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <utility>
#include <vector>

namespace strata::program {
struct Split26Fixed {
    using Id = std::pair<int32_t, int32_t>;
    static constexpr int64_t stride = 1382400, max_loan = 1862;
    static constexpr int64_t physical[2] = {9103, 8962};
    static constexpr int64_t logical[2] = {9056, 8962};
    std::array<std::vector<Id>, 2> slots;
    std::vector<Id> holes;
    std::vector<int32_t> owner, destination, old_owner, old_destination;
    struct Entry {
        int32_t owner, slot, layer, expert, old_slot;
        int32_t index() const { return layer * 512 + expert; }
    };
    struct Loan {
        int32_t origin = -1, first = -1;
        int64_t k = 0;
        std::vector<Entry> refills, holdouts, hidden, old_order;
    };
    static uint64_t hash(const uint8_t* b, size_t n, uint64_t h = 14695981039346656037ull) {
        for (size_t i = 0; i < n; ++i) h = (h ^ b[i]) * 1099511628211ull;
        return h;
    }
    // Ordered records: five signed 32-bit fields, little-endian two's-complement.
    static uint64_t hash_entries(const std::vector<Entry>& v) {
        uint64_t h = 14695981039346656037ull;
        for (const auto& e : v)
            for (int32_t x : {e.owner, e.slot, e.layer, e.expert, e.old_slot})
                for (unsigned b = 0; b < 4; ++b) {
                    const uint8_t u = (uint8_t) ((uint32_t) x >> (8 * b));
                    h = hash(&u, 1, h);
                }
        return h;
    }
    static bool read_pinned(const std::string& path, size_t size, uint64_t fnv,
                            std::vector<uint8_t>& bytes, std::string& err) {
        std::ifstream f(path, std::ios::binary);
        if (!f) { err = "split26: cannot open pinned input"; return false; }
        bytes.resize(size);
        f.read((char*) bytes.data(), (std::streamsize) size);
        if (f.gcount() != (std::streamsize) size || f.peek() != std::char_traits<char>::eof() ||
            hash(bytes.data(), bytes.size()) != fnv) {
            err = "split26: pinned input byte length/checksum differs"; return false;
        }
        return true;
    }
    bool load(const std::string& path, const std::string& profile_path,
              const std::vector<Id>& ranked, std::string& err) {
        std::vector<uint8_t> b, profile;
        if (!read_pinned(path, 36232, 0x8d52abd6aa77412aull, b, err) ||
            !read_pinned(profile_path, 196632, 0x780ecde37db4871full, profile, err)) return false;
        if (std::string((const char*) b.data(), 8) != "S26FIX1\n") {
            err = "split26: bad fixture header"; return false;
        }
        size_t at = 8;
        auto next = [&]() -> Id {
            int x = b[at] | (int(b[at + 1]) << 8); at += 2;
            return x == 0 ? Id{-1, -1} : Id{(x - 1) / 512, (x - 1) % 512};
        };
        owner.assign(48 * 512, -1); destination.assign(48 * 512, -1);
        holes.assign((size_t) physical[0], {-1, -1});
        int hole_count = 0;
        for (int st = 0; st < 2; ++st) {
            slots[st].clear();
            for (int32_t s = 0; s < physical[st]; ++s) {
                const Id id = next();
                slots[st].push_back(id);
                if (id.first == -1) {
                    if (st != 0 || s < physical[0] - max_loan) {
                        err = "split26: hole outside primary supported suffix"; return false;
                    }
                    ++hole_count; continue;
                }
                if (id.first < (st == 0 ? 0 : 26) || id.first >= (st == 0 ? 26 : 48) ||
                    id.second < 0 || id.second >= 512 || owner[(size_t) (id.first * 512 + id.second)] != -1) {
                    err = "split26: duplicate/out-of-range/ownership fixture identity"; return false;
                }
                owner[(size_t) (id.first * 512 + id.second)] = st;
                destination[(size_t) (id.first * 512 + id.second)] = s;
            }
        }
        if (hole_count != 47) { err = "split26: hole count"; return false; }
        for (int32_t s = 0; s < physical[0]; ++s) if (slots[0][s].first < 0) {
            holes[s] = next();
            if (holes[s].first != 26 || destination[(size_t) (holes[s].first * 512 + holes[s].second)] < 0) {
                err = "split26: invalid moved holdout"; return false;
            }
        }
        if (at != b.size()) { err = "split26: unconsumed fixture bytes"; return false; }
        // Independent exact reconstruction from the unchanged old split's ranked prefixes.
        std::array<std::vector<Id>, 2> old, expected;
        std::vector<Id> moved;
        std::vector<uint8_t> seen(48 * 512, 0);
        for (const auto& id : ranked) {
            if (id.first < 0 || id.first >= 48 || id.second < 0 || id.second >= 512 ||
                seen[(size_t) (id.first * 512 + id.second)]++) {
                err = "split26: malformed/duplicate profile"; return false;
            }
            const int st = id.first < 27 ? 0 : 1;
            if (old[st].size() < (size_t) (st == 0 ? 9399 : 8619)) old[st].push_back(id);
        }
        if (ranked.size() != 24576 || old[0].size() != 9399 || old[1].size() != 8619) {
            err = "split26: old profile extent"; return false;
        }
        for (size_t s = 0; s < old[0].size(); ++s) {
            const auto id = old[0][s];
            if (id.first == 26) {
                moved.push_back(id);
                if (s >= 9399 - max_loan) expected[0].push_back({-1, -1});
            } else expected[0].push_back(id);
        }
        expected[1] = moved;
        expected[1].insert(expected[1].end(), old[1].begin(), old[1].end());
        old_owner.assign(48 * 512, -1); old_destination.assign(48 * 512, -1);
        for (int st = 0; st < 2; ++st)
            for (int32_t slot = 0; slot < (int32_t) old[st].size(); ++slot) {
                const Id id = old[st][slot];
                old_owner[(size_t) (id.first * 512 + id.second)] = st;
                old_destination[(size_t) (id.first * 512 + id.second)] = slot;
            }
        if (moved.size() != 343 || expected != slots) {
            err = "split26: fixture differs from exact old ranked membership/order"; return false;
        }
        for (int32_t s = (int32_t) (physical[0] - max_loan); s < physical[0]; ++s)
            if ((slots[0][s].first < 0 ? holes[s] : slots[0][s]) != old[0][(size_t) s + 296]) {
                err = "split26: old-origin suffix order"; return false;
            }
        return true;
    }
    bool plan(int origin, int64_t k, Loan& out, std::string& err) const {
        if (origin < 0 || origin > 1 || k < 0 || k > max_loan ||
            slots[origin].size() != (size_t) physical[origin]) {
            err = "split26: unsupported origin/physical suffix"; return false;
        }
        out = Loan{};
        out.origin = origin; out.k = k; out.first = (int32_t) (physical[origin] - k);
        for (int32_t s = out.first; s < physical[origin]; ++s) {
            const bool hole = slots[origin][s].first < 0;
            const Id id = hole ? holes[s] : slots[origin][s];
            const int32_t i = id.first * 512 + id.second;
            const Entry e{owner[(size_t) i], destination[(size_t) i], id.first, id.second,
                          origin == 0 ? s + 296 : s - 343};
            if (e.owner < 0 || e.slot < 0 || (hole && e.owner != 1) || (!hole && e.owner != origin)) {
                err = "split26: loan identity/destination mismatch"; return false;
            }
            (hole ? out.holdouts : out.refills).push_back(e);
            out.old_order.push_back(e); out.hidden.push_back(e);
        }
        auto by_id = [](const Entry& a, const Entry& b) { return a.index() < b.index(); };
        std::sort(out.refills.begin(), out.refills.end(), by_id);
        std::sort(out.hidden.begin(), out.hidden.end(), by_id);
        return true;
    }
};
}  // namespace strata::program
