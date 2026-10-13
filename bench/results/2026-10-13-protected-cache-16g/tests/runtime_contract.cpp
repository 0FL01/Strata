#include "strata/core/conversation_cache.hpp"
#include "strata/core/conversation_memory_budget.hpp"
#include "strata/program/coverage.hpp"
#include <cassert>
#include <iostream>
#include <limits>
using namespace strata::core;
namespace cov = strata::program::coverage;
ConversationCheckpoint ck(int n, int value=1, int64_t target=0) {
    ConversationCheckpoint c;
    c.ids.assign(n,value); c.gdn.assign(8,1); c.ple.assign(2,3);
    c.tails.assign(4,2);c.dead.assign(2,4);c.block_pos.assign(4,0);
    c.coverage_target=target;c.used=n;
    return c;
}
SavedConversation image(int value) {
    SavedConversation c;c.live=ck(40,value);
    c.checkpoints.push_back(ck(16,value,16));
    c.coverage_trusted=true;c.coverage_hole=uint8_t(cov::HoleReason::budget);c.coverage_hole_target=32;
    return c;
}
int main() {
    // Same subtraction guard used by protected GEN admission, before consumed.reserve.
    auto fits = [](int64_t n, int64_t max_new, int64_t maximum) {
        return !(n > maximum - 8 || max_new > maximum - n - 8);
    };
    assert(fits(130900,512,262144));
    assert(fits(262135,1,262144));
    assert(!fits(262136,1,262144));
    assert(!fits(1,std::numeric_limits<int64_t>::max(),262144));
    assert(!fits(0,1,1));
    // Runtime metadata survives stage split, ordinary core deep-copy and merge.
    std::vector<ConversationCheckpoint> bank;
    auto c=ck(32,7,16);c.imgs.push_back({3,123});c.stage_parts.push_back(ck(32,7));
    bank.push_back(c);
    auto split=conversation_checkpoints_split(std::move(bank),1);
    assert(split.parts[0][0].coverage_target==16);
    assert(split.parts[0][0].imgs==c.imgs);
    auto parked0=split.stage0, parked1=split.parts[0]; // historical snapshot_save uses vector assignment
    ConversationCheckpointSplit restored;restored.stage0=parked0;restored.parts.push_back(parked1);
    assert(conversation_checkpoints_merge(std::move(restored),bank));
    assert(bank[0].coverage_target==16 && bank[0].stage_parts[0].coverage_target==16);
    assert(bank[0].ids==c.ids && bank[0].imgs==c.imgs && bank[0].gdn==c.gdn);
    // Reject mismatched role/image metadata, not just mismatched token counts.
    auto bad=conversation_checkpoints_split(std::move(bank),1);bad.parts[0][0].coverage_target=0;
    assert(!conversation_checkpoints_merge(std::move(bad),bank));

    // The selected image is detached BEFORE global admission evicts/deindexes neighbors.
    ConversationCache cache(1<<20,4);
    cache.put(image(1));cache.put(image(2));cache.put(image(3));
    std::vector<int32_t> query(50,2);
    auto match=cache.best(query,{},true);assert(match.tokens==40);
    auto selected=cache.take(match.index);size_t held=selected.bytes();
    assert(cache.make_room_global(0,held,held+image(3).bytes()));
    assert(selected.live.ids[0]==2); // stale-index regression
    assert(selected.coverage_trusted && selected.coverage_hole_target==32);

    // Active + selected + retained + multipart captures + parking overlap share one controller.
    ConversationMemoryBudget budget(4096);ConversationMemoryInventory inv;
    inv.active=1024;inv.parked=1000;inv.selected=500;inv.retained=500;inv.metadata=64;
    assert(budget.reconcile(inv));
    {
        auto ticket=budget.reserve(900);assert(ticket);assert(budget.snapshot().total==3988);
        assert(!budget.reserve(109));
        inv.inflight=900;assert(ticket.commit(inv));assert(budget.snapshot().reserved==0);
        auto fail=budget.reserve(109);assert(!fail);
    }
    inv.inflight=0;assert(budget.reconcile(inv));
    // All-stage reservation covers partial payload destruction before its own destructor.
    {
        auto ticket=budget.reserve(900);std::vector<ConversationCheckpoint> partial(2);
        partial[0]=ck(16); // other stage missing: no publish/no scheduler advancement
        cov::State state(16,128);assert(state.due(16));state.failed(16,cov::HoleReason::incomplete_snapshot);
        assert(state.next_target==16 && state.has_hole());
    }
    assert(budget.snapshot().reserved==0);
    assert(conversation_cache_add(SIZE_MAX,1)==SIZE_MAX);
    assert(conversation_cache_product(SIZE_MAX,2)==SIZE_MAX);
    std::cout<<"runtime host integration contracts: PASS\n";
}
