#include "strata/program/conv_cache.hpp"
#include "strata/core/conversation_cache.hpp"
#include <cassert>
#include <iostream>
#include <memory>
using namespace strata::program::conv_cache;
using namespace strata::core;
struct Item { int64_t n; uint64_t stamp; bool tail=false; };
struct Pool {
    std::vector<Item> v; uint64_t clock=0; bool coverage=true;
    void add(int64_t n, bool tail=false) {
        for (auto& x:v) if(x.n==n) {x.stamp=++clock; if(!tail)x.tail=false; return;}
        if(tail) std::erase_if(v,[](auto x){return x.tail;});
        v.push_back({n,++clock,tail});
        while(v.size()>6) {
            std::vector<uint64_t> stamps; std::vector<int64_t> lengths;
            std::unique_ptr<bool[]> tails(new bool[v.size()]);
            for(size_t i=0;i<v.size();++i){stamps.push_back(v[i].stamp);lengths.push_back(v[i].n);tails[i]=v[i].tail;}
            size_t k=coverage ? spread_victim(lengths.data(),stamps.data(),v.size(),6,tails.get(),nullptr) : eviction_victim(stamps.data(),v.size(),6,tails.get());
            if(k==v.size())break;
            v.erase(v.begin()+k);
        }
        assert(v.size()<=6);
    }
    int64_t resume(int64_t n)const{int64_t best=0;for(auto x:v)if(x.n<=n)best=std::max(best,x.n);return best;}
};
ConversationCheckpoint cp(int n,int value=1){ConversationCheckpoint c;c.ids.assign(n,value);c.gdn.resize(8);return c;}
SavedConversation img(int n,std::initializer_list<int> points){SavedConversation e;e.live=cp(n);for(int x:points)e.checkpoints.push_back(cp(x));return e;}
int main(){
    Pool p, old;old.coverage=false;
    for(auto* q:{&p,&old}){
        q->add(10665);
        for(int64_t n=27049;n<147456;n+=16384)q->add(n);
        q->add(147657);
        for(int64_t n=148000;n<150000;n+=100)q->add(n);
    }
    assert(old.resume(147658)==10665);
    assert(p.resume(147658)>10665);
    // Repeated short additions retain useful middle history at exactly six slots.
    Pool all;
    for(int64_t n=16384;n<=262144;n+=16384)all.add(n);
    for(int64_t n=262145;n<275000;++n)all.add(n);
    assert(all.v.size()==6 && all.resume(250000)>16384);
    // Tail replacement must never claim/promote disposable checkpoints into the anchor pool.
    Pool tails; tails.add(10665); tails.add(147657);
    for(int64_t n=148000;n<152000;n+=100){tails.add(n,true);tails.add(n+1);}
    assert(tails.resume(147658)>10665);
    // Branch/cancellation pruning remains external and authoritative: discard overwritten positions.
    std::erase_if(p.v,[](auto x){return x.n>147658;});
    p.add(147658); p.add(147800); assert(p.resume(147658)==147658);
    std::erase_if(p.v,[](auto x){return x.n>120000;}); // partial cancellation/rewind
    for(auto x:p.v)assert(x.n<=120000);
    // A newer deepest checkpoint cannot replace an older unique ancestor's recurrent state.
    ConversationCache cache(1<<20,8);
    auto a=img(30,{10,20});assert(cache.put(std::move(a)));auto bytes=cache.bytes();
    auto only_deep=std::vector<ConversationCheckpoint>{cp(20)};
    assert(cache.drop_superseded(cp(40).ids,{},only_deep,true)==0);
    assert(cache.bytes()==bytes && cache.size()==1);
    auto all_points=std::vector<ConversationCheckpoint>{cp(10),cp(20)};
    assert(cache.drop_superseded(cp(40).ids,{},all_points,false)==0);
    all_points[0].imgs={{2,99}};
    assert(cache.drop_superseded(cp(40).ids,{},all_points,true)==0);
    all_points[0].imgs.clear();all_points[0].ids[0]=2;
    assert(cache.drop_superseded(cp(40).ids,{},all_points,true)==0);
    all_points[0]=cp(10);
    assert(cache.drop_superseded(cp(20).ids,{},std::vector<ConversationCheckpoint>{cp(10)},true)==1);
    assert(cache.bytes()==0 && cache.size()==0);
    // Preserve unique ancestors but remain strictly bounded by parked slots and bytes.
    ConversationCache bounded(4096,2);
    for(int i=1;i<30;++i){auto e=img(30+i,{i});assert(bounded.put(std::move(e)));assert(bounded.size()<=2 && bounded.bytes()<=4096);}
    assert(bounded.evictions()>0);
    auto huge=img(2000,{100}); const auto before=bounded.bytes();
    assert(!bounded.put(std::move(huge)));assert(bounded.bytes()==before);
    std::cout<<"spread regression passed: short turns, 147658 compaction, tails, pruning, identity, superseded, count/bytes\n";
}
