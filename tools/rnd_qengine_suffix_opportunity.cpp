#include "strata/spec/suffix_drafter.hpp"
#include <cstdint>
#include <iostream>
#include <vector>
// Offline opportunity screen only: overlapping proposals are not a speed estimate.
// stdin: prompt_count output_count, followed by prompt IDs and output IDs.
int main() {
 size_t np=0, no=0;
 if (!(std::cin>>np>>no) || np>1048576 || no>65536) return 2;
 std::vector<int32_t> p(np),o(no);
 for(auto& t:p) if(!(std::cin>>t)) return 2;
 for(auto& t:o) if(!(std::cin>>t)) return 2;
 strata::spec::SuffixDrafter d(3,64,np+no+1);
 d.append(p.data(),p.size());
 uint64_t proposed=0, useful2=0, useful3=0, accepted=0;
 for(size_t i=0;i<no;++i) {
  int32_t out[6]; int k=d.propose(6,out), a=0;
  while(a<k && i+(size_t)a<no && out[a]==o[i+a]) ++a;
  proposed+=(k>0); useful2+=(a>=2); useful3+=(a>=3); accepted+=a;
  d.append(o[i]);
 }
 std::cout<<"{\"positions\":"<<no<<",\"proposed_positions\":"<<proposed
          <<",\"accepted_prefix_sum_overlapping\":"<<accepted
          <<",\"positions_with_2_correct\":"<<useful2
          <<",\"positions_with_3_correct\":"<<useful3<<"}\n";
}
