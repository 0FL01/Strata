#include "strata/core/conversation_cache.hpp"
#include <cassert>
#include <iostream>
#include <type_traits>
#include <utility>
using namespace strata::core;
int main() {
    ConversationCheckpoint cp;
    cp.ids = {1, 2, 3}; cp.imgs = {{1, 42}}; cp.used = 99; cp.coverage_target = 16384;
    cp.gdn = {10}; cp.stage_parts.resize(2); cp.stage_parts[0].gdn = {20}; cp.stage_parts[1].gdn = {30};
    std::vector<ConversationCheckpoint> bank;
    bank.push_back(cp);
    ConversationCheckpoint incomplete; incomplete.ids = {8}; incomplete.coverage_target = 32768;
    bank.push_back(incomplete);
    auto split = conversation_checkpoints_split(std::move(bank), 2);
    assert(split.stage0.size() == 1 && split.rest.size() == 1);
    assert(split.stage0[0].coverage_target == 16384 && split.rest[0].coverage_target == 32768);
    for (const auto& part : split.parts) {
        assert(part.size() == 1 && part[0].coverage_target == 16384);
        assert(part[0].ids == cp.ids && part[0].imgs == cp.imgs && part[0].used == cp.used);
    }
    std::vector<ConversationCheckpoint> merged;
    assert(conversation_checkpoints_merge(std::move(split), merged));
    assert(merged.size() == 2 && merged[0].coverage_target == 16384 && merged[1].coverage_target == 32768);
    assert(merged[0].stage_parts.size() == 2 && merged[0].stage_parts[0].gdn == std::vector<uint8_t>{20});
    SavedConversation image;
    image.coverage_trusted = true; image.coverage_hole = 2; image.coverage_hole_target = 32768;
    image.checkpoints = std::move(merged);
    auto copy = image;
    auto moved = std::move(copy);
    assert(moved.coverage_trusted && moved.coverage_hole == 2 && moved.coverage_hole_target == 32768);
    assert(moved.checkpoints[0].coverage_target == 16384);
    std::cout << "checkpoint split/merge and parked metadata copy/move passed\n";
}
