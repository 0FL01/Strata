#include "strata/core/conversation_cache.hpp"
#include "strata/program/coverage.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
using namespace strata::core;
namespace cov = strata::program::coverage;
ConversationCheckpoint point(int64_t length, uint64_t used, int64_t target=0) {
    ConversationCheckpoint c;c.ids.assign(size_t(length),7);c.used=used;c.coverage_target=target;
    return c;
}
void trim(std::vector<ConversationCheckpoint>& bank) {
    for (;;) {
        std::vector<int64_t> lengths,targets;std::vector<uint64_t> stamps;
        for(const auto&c:bank){lengths.push_back(c.ids.size());targets.push_back(c.coverage_target);stamps.push_back(c.used);}
        auto v=cov::eviction_victim(lengths.data(),stamps.data(),targets.data(),bank.size());
        if(!v)return;
        bank.erase(bank.begin()+std::ptrdiff_t(*v));
    }
}
int64_t best(const std::vector<ConversationCheckpoint>& bank,int64_t lcp) {
    std::vector<int32_t> query(size_t(lcp+10),7);query[size_t(lcp)]=8;
    int64_t found=0;
    for(const auto&c:bank)found=std::max(found,conversation_prefix(c,query,{}));
    return found;
}
bool has(const std::vector<ConversationCheckpoint>& b,int64_t n) {
    return std::any_of(b.begin(),b.end(),[&](const auto&c){return int64_t(c.ids.size())==n;});
}
int main() {
    const auto base=std::vector<ConversationCheckpoint>{point(100,1),point(16384,2,16384),point(32768,3,32768)};
    auto v2=base;v2.push_back(point(33000,4));trim(v2);v2.push_back(point(34000,6));trim(v2);
    assert(has(v2,33000)&&has(v2,34000)); // two existing ordinary snapshots, plus root+anchors
    auto v1=base;v1.push_back(point(33000,4));trim(v1);v1.push_back(point(33100,5));trim(v1);
    v1.push_back(point(34000,6));trim(v1);v1.push_back(point(34100,7));trim(v1);
    assert(!has(v1,33000)&&has(v1,34000)&&has(v1,34100));
    assert(best(v2,33050)==33000 && best(v1,33050)==32768); // v2 improves an older turn rewind

    // Plain continuation creates no new turn snapshot. This is a concrete lost optional endpoint in v2.
    v1.push_back(point(34300,8));trim(v1);
    assert(best(v1,34200)==34100);
    assert(best(v2,34200)==34000); // 100 extra tokens, not a missing protected anchor
    for(int64_t n:{16384,32768})assert(has(v1,n)&&has(v2,n));
    auto live=point(34300,8);std::vector<int32_t> continuation(34302,7);
    assert(conversation_prefix(live,continuation,{})==34300); // unchanged immediate continuation

    SavedConversation saved;saved.live=live;saved.checkpoints=v2;saved.coverage_trusted=true;
    ConversationCache parked(16<<20,4);assert(parked.put(std::move(saved)));
    auto match=parked.best(continuation,{},true);assert(match.live&&match.tokens==34300);
    auto restored=parked.take(match.index);assert(restored.live.ids==live.ids);
    assert(restored.checkpoints.size()==v2.size()); // parking has its own terminal live state

    // Prompts without turn tokens have no ordinary snapshots to recycle. Empty recent slots are intentional.
    auto no_turn_v2=std::vector<ConversationCheckpoint>{point(16384,1,16384),point(32768,2,32768)};
    auto no_turn_v1=no_turn_v2;no_turn_v1.push_back(point(40000,3));trim(no_turn_v1);
    no_turn_v1.push_back(point(40500,4));trim(no_turn_v1);
    assert(best(no_turn_v1,40200)==40000);
    assert(best(no_turn_v2,40200)==32768);
    assert(40200-best(no_turn_v2,40200)<16384); // optional off-grid benefit lost, protected coverage unchanged
    auto no_turn_live=point(40500,4);std::vector<int32_t> no_turn_continuation(40502,7);
    assert(conversation_prefix(no_turn_live,no_turn_continuation,{})==40500);
    cov::State no_turn_coverage(16384,262144);
    int64_t nt_lengths[]={16384,32768},nt_targets[]={16384,32768};
    assert(no_turn_coverage.rebuild(nt_lengths,nt_targets,2,40500,true));
    assert(no_turn_coverage.next_target==49152);

    // Every due decode boundary is still published, including the last EOS/cancel/max token window.
    cov::State coverage(16384,262144);auto anchors=base;
    int64_t lengths[]={100,16384,32768},targets[]={0,16384,32768};
    assert(coverage.rebuild(lengths,targets,3,32768,true));
    for(int64_t endpoint:{int64_t(49151),int64_t(49156)}) {
        if(coverage.due(endpoint)){const int64_t target=coverage.saved(endpoint);anchors.push_back(point(endpoint,10,target));}
    }
    assert(coverage.next_target==65536 && has(anchors,49156));
    // Cancelling a partially read prompt does not add an invalid terminal state; previous anchors remain.
    auto cancelled_bank=anchors;trim(cancelled_bank);assert(has(cancelled_bank,49156));
    assert(!has(cancelled_bank,50000));
    std::cout<<"recent retention v2 contracts: PASS\n";
}
