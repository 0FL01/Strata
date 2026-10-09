#!/usr/bin/env python3
"""Check the published numeric derivative, not hardware or omitted provenance."""
import argparse
import copy
import json
import math
from pathlib import Path

def need(v,why):
    if not v: raise ValueError(why)
def close(a,b,why):
    need(math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11),why)
def validate(m,c):
    rows=m['results'];need([r['tag'] for r in rows]==['A1','B1','B2','A2'],'order')
    for r in rows:
        need(r['passed'] is True and r['prompt_tokens']==65536 and r['actual_outputs']==1024,'coverage')
        need(len(r['output_ids'])==1024 and all(type(i)is int and 0<=i<248320 for i in r['output_ids']),'IDs')
        need(r['output_ids']==rows[0]['output_ids'],'full parity')
        for k in ['accepted','offered','cache_hits','lookups','prompt_read','prompt_reused']:
            need(r[k]==rows[0][k],'counters')
        need(r['prompt_read']==65536 and r['prompt_reused']==0,'reuse')
        for key,count,ms in [('PP',65536,'prompt_ms'),('TG',1024,'decode_ms')]:
            need(math.isfinite(r[ms]) and r[ms]>0,'duration');close(r[key],count*1000/r[ms],'rate')
    for key in ['PP','TG']:
        a=(rows[0][key]+rows[3][key])/2;b=(rows[1][key]+rows[2][key])/2;d=m['decision'][key]
        close(a,d['stable_mean'],'A mean');close(b,d['candidate_mean'],'B mean');close(100*(b/a-1),d['gain_pct'],'gain')
        need(len(d['paired_gain_pct'])==2,'pairs')
        for (ai,bi),saved in zip([(0,1),(3,2)],d['paired_gain_pct']):
            g=100*(rows[bi][key]/rows[ai][key]-1);close(g,saved,'pair gain');need(g>0,'positive pair')
    need(m['decision']['all1024_ids_equal'] is True and m['decision']['all_counters_equal'] is True,'decision')
    need(c['benchmark_passed'] is True and c['cross_gpu_full_output_equal'] is True,'component pass')
    need([g['gpu_ordinal'] for g in c['GPUs']]==[0,1],'GPU coverage')
    for g in c['GPUs']:
        need(g['passed'] is True and g['exit_code']==0 and g['selected_route_smoke'] is True,'route/completion')
        t=g['measurement'];r=t['process_medians_ms'];need(set(r)=={'A1','B1','B2','A2'},'component arms')
        need(all(math.isfinite(v) and v>0 for v in r.values()),'positive medians')
        a=(r['A1']+r['A2'])/2;b=(r['B1']+r['B2'])/2
        close(a,t['A_mean_ms'],'component A');close(b,t['B_mean_ms'],'component B');close(100*(a-b)/a,t['component_latency_reduction_pct'],'component gain')
        h=g['full_output_sha256'];need(set(h)=={'A1.bin','A2.bin','B1.bin','B2.bin','route-smoke.bin','edge1-A.bin','edge1-B.bin','edge33-A.bin','edge33-B.bin'},'hash coverage')
        need(all(len(v)==64 and all(ch in '0123456789abcdef' for ch in v) for v in h.values()),'hash format')
        need(len({h[k] for k in ['A1.bin','A2.bin','B1.bin','B2.bin','route-smoke.bin']})==1,'main hash parity')
        need(h['edge1-A.bin']==h['edge1-B.bin'] and h['edge33-A.bin']==h['edge33-B.bin'],'edge parity')
        need(h==c['GPUs'][0]['full_output_sha256'],'cross GPU hashes')
    need(c['ISA']['gate_passed'] is True,'ISA gate')
    for arm,v,s,sh in [('A',42,42,70),('B',48,43,26)]:
        x=c['ISA']['arms'][arm];res=x['compiler_resources']
        need(x['full_kernel']['ds_bpermute_b32']==sh and x['full_kernel']['v_fmac_f32_e32']==87,'full ISA')
        need(x['score_region']['ds_bpermute_b32']==(60 if arm=='A' else 16) and x['score_region']['v_add_f32_e32']==(60 if arm=='A' else 16) and x['score_region']['v_fmac_f32_e32']==84,'score ISA')
        need(res['VGPRs']==v and res['TotalSGPRs']==s and res['Occupancy [waves/SIMD]']==4 and res['LDS Size [bytes/block]']==15872,'resources')
        need(all(res[k]==0 for k in ['ScratchSize [bytes/lane]','SGPRs Spill','VGPRs Spill']),'spills')
    return {'passed':True,'scope':'numeric derivative consistency only'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('component',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args();m=json.loads(a.model.read_text());c=json.loads(a.component.read_text());out=validate(m,c)
    if a.selftest:
        cases=[
          lambda m,c:m['results'][1]['output_ids'].__setitem__(900,0),
          lambda m,c:m['results'][2]['output_ids'].pop(),
          lambda m,c:m['results'][0].__setitem__('PP',1),
          lambda m,c:m['decision']['TG'].__setitem__('gain_pct',99),
          lambda m,c:m['results'][1].__setitem__('accepted',0),
          lambda m,c:m['results'][0].__setitem__('prompt_ms',-1),
          lambda m,c:c['GPUs'][0]['measurement']['process_medians_ms'].__setitem__('B1',10),
          lambda m,c:c['GPUs'][1]['full_output_sha256'].__setitem__('B1.bin','0'*64),
          lambda m,c:c['GPUs'][0].__setitem__('selected_route_smoke',False),
          lambda m,c:c['GPUs'][1].__setitem__('exit_code',1),
          lambda m,c:c['ISA']['arms']['B']['compiler_resources'].__setitem__('ScratchSize [bytes/lane]',4),
          lambda m,c:c['ISA']['arms']['B']['score_region'].__setitem__('ds_bpermute_b32',60),
        ]
        for mutate in cases:
            mm,cc=copy.deepcopy(m),copy.deepcopy(c);mutate(mm,cc)
            try:validate(mm,cc)
            except (ValueError,KeyError,TypeError):pass
            else:raise ValueError('missed corruption')
        out['negative_cases_rejected']=len(cases)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
