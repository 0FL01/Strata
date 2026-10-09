#!/usr/bin/env python3
"""Offline arithmetic, identity, parity and claim checks; no hardware/API calls."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
STABLE='ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14'
CANDIDATE='c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049'
PROFILES={'A':'01e127c02d2537022758b95945aaf5c600ad950c1008594205fb1cfb8b31ac5a','B':'058cf74783eb8d107b3c82122a94adc196f6f0f9cab18b76e5eb6e0e4df60f6d'}
TAGS=['A1','B1','B2','A2']
OPTIONAL=['lookup_chain_accepted','lookup_chain_offered','native_suffix_accepted','native_suffix_offered','decode_windows']
COUNTERS=['accepted','offered','cache_hits','lookups','prompt_reused','prompt_read','ram_blobs','file_blobs','file_read_mb','offloaded_experts']+OPTIONAL

def need(ok,label):
    if not ok:raise ValueError(label)
def close(a,b,label):need(math.isfinite(a) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),label)
def digest(v):return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def canonical_hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def counters(r):return {**{k:r[k] for k in COUNTERS},**{'suffix_'+k:r['suffix_drafts'][k] for k in ['windows','accepted','offered']}}

def validate(d):
    need(not any(p in json.dumps(d) for p in ['/home/','/workspace/','/src/','/models/','/sata/']),'no private absolute paths')
    s=d['summary'];rows=s['results'];decision=s['decision'];need([r['tag'] for r in rows]==TAGS,'complete ABBA order')
    need(s['measurement_completed'] and s['quality_passed'] and s['owned_containers_cleaned'] and d['standalone_results_match_summary'],'completion/parity/cleanup')
    need(s['stable_binary_sha256']==STABLE and s['candidate_binary_sha256']==CANDIDATE,'binary identities')
    need(not s['api_touched'] and not s['stable_configuration_modified_by_runner'] and not s['promoted'],'API/stable/promotion scope')
    need(s['constant_workload_claim'] is False and decision['constant_workload_claim'] is False,'no constant-work proof claim')
    need(s['performance_gate']=='report-only; no throughput threshold and no automatic retries','predeclared report-only scope')
    need(s['fixture_sha256']=='63ce3d4042027a00b2193feab143f1d9443b5c31a863a962ec9543ccb54d9695','fixture identity')
    need(s['reference_sha256']=='9a0542235ff1f7d195260b672ff12683775fc0132dbcf25c9c9836a2c30bb6a3','historical reference identity')
    need(s['candidate_build_receipt_sha256']=='ab206a42b4984015f21a9e72b2aac402292b35fb995b8395631ef5256f9f9104','candidate build receipt')
    need(s['candidate_64k_summary_sha256']=='d3a598015014e1301197b2041ca9ae54618eb023bdd27b06ce1cfc03030ade12' and s['candidate_correctness_summary_sha256']=='bf659ce6acc2efa1e0baa6a60023658970598777bdcd69527569b5b5a8c44162','candidate qualification provenance')
    sources=s['candidate_compiled_source_sha256'];need(len(sources)==7 and all(digest(v) for v in sources.values()),'seven source hashes')
    need(sources['src/kernels/cuda/qsa_select.cu']=='8d836acd211b7e493cd50bd680d128489f3f25f94ea26725afbab2402ef899bc' and sources['src/program/generate.cpp']=='e7a5a754af2155c779aad5f2232ba1c0052ebbd2a4795d40885eff571b62221c','selector/host source identity')
    history=s['historical_default_output_ids'];need(len(history)==1024,'complete historical reference')
    for r in rows:
        need(r['passed'] and r['prompt_tokens']==65536 and r['actual_outputs']==len(r['output_ids'])==1024,'64K/1024 output coverage')
        need(all(type(i)is int and 0<=i<248320 for i in r['output_ids']) and r['output_ids']==history,'full exact output IDs')
        for rate,n,ms in [('PP',65536,'prompt_ms'),('TG',1024,'decode_ms')]:
            need(math.isfinite(r[ms]) and r[ms]>0,'positive duration');close(r[rate],n*1000/r[ms],'native throughput arithmetic')
        need(r['native_done_field_count']==16 and r['optional_chain_counters_available'] is False and all(r[k] is None for k in OPTIONAL),'unavailable optional counters remain null')
        need(r['prompt_reused']==0 and r['prompt_read']==65536,'full fresh prompt')
        need(all(isinstance(r[k],(int,float)) and math.isfinite(r[k]) and r[k]>=0 for k in COUNTERS if k not in OPTIONAL),'counter domain')
        m=d['manifests'][r['tag']];arm=r['tag'][0]
        need(m['release_binary_sha256']==(STABLE if arm=='A' else CANDIDATE) and m['native_exit']==0 and m['fresh_process'],'fresh release process')
        need(canonical_hash(m['flags'])==PROFILES[arm],'exact per-release performance flags')
        need(m['full_native_args_sha256']=='d94b0bb9ffb0463dcce52afe87bb57d8e8ea3c2d037ca2022b254b77b099d953','identical original native args')
        need(m['fixture_sha256']==s['fixture_sha256'] and m['sampling']=={'temperature':0,'top_p':1,'top_k':1,'seed':12345},'fixture/sampling provenance')
        info=r['engine_info'];need(info==m['engine_info']==rows[0]['engine_info'],'identical engine topology')
        for k,v in {'context':'204800','kv':'int8','kv_resident':'32768','expert_slots':'19078','expert_slots_primary':'9900','spec':'6','mtp_max':'4','lookup':'3'}.items():need(info[k]==v,'default topology')
        opts=m['native_options'];need(opts['--spec']=='4' and '--suffix-draft' not in opts and '--mtp-max-t' not in opts and opts['--layer-split']=='27' and opts['--adapt-every']=='0','original default request options')
        close(r['request_wall_s'],m['request_wall_s'],'request-time provenance');close(r['load_wall_s'],m['load_wall_s'],'load-time provenance')
        need(digest(m['stderr_content_sha256']) and all(digest(h) for h in m['native_forensics_sha256'].values()),'private evidence hashes only')
        t=d['thermal_summary'][r['tag']];need(t['sample_count']==27 and t['all_power_high'] and t['all_power_caps_190w'],'recorded thermal/power coverage')
        need(all(t['max_temperature_millicelsius'][k]<v for k,v in [('temp1_input',80000),('temp2_input',90000),('temp3_input',90000)]),'observed thermal ceilings')
    values=[counters(r) for r in rows]
    need(decision['all1024_ids_equal'] and decision['all_topology_equal'] and decision['all_counters_equal']==all(v==values[0] for v in values),'observed parity/counter equality')
    need(set(decision['unavailable_counter_fields'])==set(OPTIONAL),'explicit optional unavailability')
    for idx,(ai,bi) in enumerate([(0,1),(3,2)]):
        pair=decision['paired_counter_deltas'][idx];need(pair['pair']==rows[bi]['tag']+'/'+rows[ai]['tag'],'pair labels')
        for key in values[ai]:
            x,y=values[ai][key],values[bi][key]
            if x is None or y is None:need(pair['candidate_minus_control'][key] is None,'missing is not zero')
            else:close(pair['candidate_minus_control'][key],y-x,'explicit paired counter delta')
    for key in ['PP','TG']:
        a=(rows[0][key]+rows[3][key])/2;b=(rows[1][key]+rows[2][key])/2;value=decision[key]
        close(value['stable_mean'],a,'stable arithmetic mean');close(value['candidate_mean'],b,'candidate arithmetic mean');close(value['gain_pct'],100*(b/a-1),'direct measured gain')
        need(len(value['paired_gain_pct'])==2,'both pair gains')
        for reported,ai,bi in zip(value['paired_gain_pct'],[0,3],[1,2]):close(reported,100*(rows[bi][key]/rows[ai][key]-1),'paired measured gain')
    need(set(d['source_sha256'])=={'summary.json'}|{tag+suffix for tag in TAGS for suffix in ['.result.json','.manifest.json','.gpu-samples.json']},'complete original source coverage')
    need(all(digest(v) for v in d['source_sha256'].values()),'source hash format')
    return {'passed':True,'PP_gain_pct':decision['PP']['gain_pct'],'TG_gain_pct':decision['TG']['gain_pct'],'all_available_counters_equal':decision['all_counters_equal'],'constant_workload_proof':False,'scope':'offline consistency only; no hardware execution'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('receipt',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args();d=json.loads(a.receipt.read_text());result=validate(d)
    if a.selftest:
        mutations=[lambda x:x['summary']['results'][1]['output_ids'].__setitem__(900,-1),lambda x:x['summary']['results'][2]['output_ids'].pop(),lambda x:x['summary']['results'][0].__setitem__('PP',1),lambda x:x['summary']['decision']['TG'].__setitem__('gain_pct',99),lambda x:x['summary']['decision']['PP']['paired_gain_pct'].__setitem__(1,99),lambda x:x['summary']['results'][1].__setitem__('offered',873),lambda x:x['summary']['decision']['paired_counter_deltas'][1]['candidate_minus_control'].__setitem__('cache_hits',1),lambda x:x['summary']['results'][0].__setitem__('lookup_chain_offered',0),lambda x:x['summary']['decision'].__setitem__('constant_workload_claim',True),lambda x:x['manifests']['B1'].__setitem__('release_binary_sha256',STABLE),lambda x:x['manifests']['A1']['flags'].__setitem__('STRATA_PRIMARY_COMMIT_OVERLAP','1'),lambda x:x['summary'].__setitem__('api_touched',True),lambda x:x['thermal_summary']['B2']['max_temperature_millicelsius'].__setitem__('temp2_input',95000),lambda x:x['summary'].__setitem__('candidate_64k_summary_sha256','0'*64)]
        for change in mutations:
            bad=copy.deepcopy(d);change(bad)
            try:validate(bad)
            except (ValueError,KeyError,TypeError):pass
            else:raise RuntimeError('missed corruption')
        result['negative_cases_rejected']=len(mutations)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
