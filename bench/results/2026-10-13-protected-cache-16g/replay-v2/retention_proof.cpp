#include "proof-conv_cache.hpp"
#include "proof-conversation_cache.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using strata::program::conv_cache::spread_victim;
struct Point { int64_t len; uint64_t used; };
using Bank=std::vector<Point>;
int64_t add(Bank& bank,int64_t len,uint64_t used) {
 bank.push_back({len,used}); if(bank.size()<=6)return -1;
 std::vector<int64_t> lens;std::vector<uint64_t> stamps;
 for(auto p:bank){lens.push_back(p.len);stamps.push_back(p.used);}
 auto victim=spread_victim(lens.data(),stamps.data(),bank.size(),6,nullptr,nullptr);
 auto result=bank[victim].len;bank.erase(bank.begin()+victim);return result;
}
int64_t resume(const Bank& bank){int64_t result=0;for(auto p:bank)if(p.len<=117131)result=std::max(result,p.len);return result;}
void print(const Bank& bank){for(auto p:bank)std::cout<<p.len<<',';}
void prove_parked() {
 using strata::core::ConversationCheckpoint;
 using strata::core::ConversationCache;
 using strata::core::SavedConversation;
 const std::vector<int64_t> init{10674,18866,35250,51634,68018,84402,100786,117170,128556};
 const std::vector<int64_t> turns{133472,135692,136089,147644,147932,148220,148508};
 // Integer/token-only snapshots: exact ownership/selection code, no tensor or byte-volume claim.
 ConversationCache parked(size_t(12288)<<20,4);
 Bank active;uint64_t stamp=0;
 for(auto n:init)add(active,n,++stamp);
 int64_t prompt_len=128561;
 std::vector<int32_t> history(prompt_len+32,7);
 for(size_t step=0;step<turns.size();++step){
  const int64_t lcp=prompt_len+16;
  std::vector<int32_t> next(history.begin(),history.begin()+lcp);
  next.push_back(history[lcp]+1);next.resize(turns[step]+5,7);
  const auto before=parked.best(next,{},true);
  assert(before.tokens<=active.back().len); // never refresh an old useful ancestor through selection
  SavedConversation image;image.live.ids=history;
  for(auto point:active){ConversationCheckpoint c;c.ids.assign(history.begin(),history.begin()+point.len);c.used=point.used;image.checkpoints.push_back(std::move(c));}
  assert(parked.put(std::move(image))); // Successful normal admission is verified separately in GPU reproduction.
  add(active,turns[step],++stamp);
  prompt_len=next.size();history=std::move(next);history.resize(prompt_len+32,7);
  std::cout<<"parked_step="<<step+1<<" lcp="<<lcp<<" turn="<<turns[step]<<" entries="<<parked.size()<<" evictions="<<parked.evictions()<<" active_resume="<<resume(active)<<'\n';
 }
 std::vector<int32_t> compact(history.begin(),history.begin()+117131);
 compact.push_back(history[117131]+1);compact.resize(134088,7);
 auto best=parked.best(compact,{},true);
 assert(resume(active)==10674&&best.tokens==10674);
 std::cout<<"whole_selection active="<<resume(active)<<" parked="<<best.tokens<<" chosen=10674 read=123414 slots="<<parked.size()<<" evictions="<<parked.evictions()<<'\n';
}
int main(int argc,char**argv){
 prove_parked();
 assert(argc==2);std::ifstream in(argv[1]);assert(in);
 std::string event;int req;int64_t len,victim=-1;uint64_t stamp;Bank bank,initial;int verified=0;
 std::vector<int64_t> candidates;
 while(in>>event>>req>>len>>stamp){
  if(event=="create"){
   if(req>1&&initial.empty())initial=bank;
   victim=add(bank,len,stamp);
   if(req>1)candidates.push_back(len);
   std::cout<<"trace_create req="<<req<<" len="<<len<<" victim="<<victim<<" resume="<<resume(bank)<<" bank=";print(bank);std::cout<<'\n';
  }else if(event=="evict"){assert(victim==len);++verified;}
  else if(event=="touch"){for(auto&p:bank)if(p.len==len)p.used=stamp;}
  else assert(false);
 }
 assert(verified==23&&resume(bank)==10674);
 std::cout<<"observed_verified="<<verified<<" final_resume="<<resume(bank)<<" initial=";print(initial);std::cout<<'\n';
 // Exact search among monotonically increasing recorded turn boundaries; last147644 required.
 for(int count=1;count<=int(candidates.size());++count){
  uint64_t tries=0;bool found=false;std::vector<int64_t> best,chosen;Bank final;
  auto recurse=[&](auto&&self,int at,Bank current)->void{
   if(found)return;
   if(int(chosen.size())==count){
    if(chosen.back()!=147644)return;
    ++tries;
    if(resume(current)==10674){found=true;best=chosen;final=current;}return;
   }
   for(int i=at;i<int(candidates.size());++i){
    if(int(candidates.size())-i<count-int(chosen.size()))break;
    // Otherwise a new request would introduce an unmodeled periodic save.
    int64_t previous=chosen.empty()?128556:chosen.back();
    if(candidates[i]-(previous+5+31)>=16384)continue;
    Bank next=current;add(next,candidates[i],10+chosen.size());chosen.push_back(candidates[i]);
    self(self,i+1,next);chosen.pop_back();if(found)return;
   }
  };
  recurse(recurse,0,initial);
  std::cout<<"search_count="<<count<<" evaluated="<<tries<<" found="<<found<<'\n';
  if(found){std::cout<<"minimal_turns="<<count<<" positions=";for(auto x:best)std::cout<<x<<',';std::cout<<" bank=";print(final);std::cout<<" resume="<<resume(final)<<" read="<<134088-resume(final)<<'\n';break;}
 }
}
