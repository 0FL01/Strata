#!/usr/bin/env python3
"""Offline FIT17 receipt consistency checks; no hardware, API, or filesystem mutation."""
import argparse
import copy
import json
import hashlib
import math
from pathlib import Path
BINARY='c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049'
BASE='ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9'
SELECT='8d836acd211b7e493cd50bd680d128489f3f25f94ea26725afbab2402ef899bc'
FIXTURE='63ce3d4042027a00b2193feab143f1d9443b5c31a863a962ec9543ccb54d9695'
TAGS=['A1','B1','B2','A2'];CORE=['accepted','offered','cache_hits','lookups','prompt_reused','prompt_read']
OPTIONAL=['lookup_chain_accepted','lookup_chain_offered','native_suffix_accepted','native_suffix_offered','decode_windows']
EXTRA=['ram_blobs','file_blobs','file_read_mb','offloaded_experts']+OPTIONAL

def need(ok,label):
    if not ok:raise ValueError(label)
def close(x,y,label):need(math.isfinite(x) and math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-11),label)
def digest(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)
def counters(row,adaptive):return {**{k:row[k] for k in CORE+(EXTRA if adaptive else [])},**{'suffix_'+k:row['suffix_drafts'][k] for k in ['windows','accepted','offered']}}

def validate(d):
    need(not any(x in json.dumps(d) for x in ['/home/','/workspace/','/src/','/models/','/sata/']),'private absolute path excluded')
    build=d['provenance']['build'];need(build['binary_sha256']==BINARY and build['base_binary_sha256']==BASE,'binary provenance')
    need(build['exit_code']==0 and build['sources_restored'] is True and build['compiler_confirmed_stopped'] is True,'build/restoration')
    need(build['feature']=='scalar FIT17 only','production scope')
    expected={**build['base_source_sha256'],'src/kernels/cuda/qsa_select.cu':SELECT};need(len(expected)==7 and build['compiled_sources']==expected,'seven compiled sources')
    need(build['patch_sha256']=='a00f7dbc888d77d32fba5b03d14a76915961016296f591b13815448d8fc2c20c','production patch')
    micro=d['provenance']['micro'];budget=micro['budget'];initial=budget['initial_gpu0'];need(initial['engineering_gate_pct']==30 and initial['first_gpu_gate_passed'] is False,'original30% failure retained')
    for r in [initial,budget['gpu1']]:
        a=sum(r['A_run_medians'])/2;b=sum(r['B_run_medians'])/2
        close(r['A_ms'],a,'micro A mean');close(r['B_ms'],b,'micro B mean');close(r['latency_reduction_pct'],100*(1-b/a),'component latency arithmetic')
    close(budget['representative_12_layer_proxy_ms_saved'],6*sum(r['A_ms']-r['B_ms'] for r in [initial,budget['gpu1']]),'proxy mean')
    close(budget['observed_extrema_12_layer_proxy_ms_saved'],6*sum(min(r['A_run_medians'])-max(r['B_run_medians']) for r in [initial,budget['gpu1']]),'proxy extrema')
    need(budget['model_gain_claim'] is False,'proxy not model gain')
    trans=micro['transitions'];need(len(trans)==micro['transition_processes']==30,'diagnostic process coverage')
    need(sum(r['cases'] for r in trans)==micro['transition_windows']==834 and sum(r['cases']*r['nq'] for r in trans)==micro['transition_rows']==4836,'diagnostic coverage')
    need(all(r['parity_passed'] and not r['timing_claim'] for r in trans),'diagnostic parity')
    outputs={};report={}
    for name,study in d['studies'].items():
        adaptive=name=='adaptive_default';s=study['summary'];rows=s['results'];need([r['tag'] for r in rows]==TAGS,'full ABBA order')
        need(study['standalone_results_match_summary'] and s['benchmark_passed'] and s['owned_containers_cleaned'],'complete receipt/cleanup')
        need(not s['api_touched'] and not s['promoted'],'API/promotion scope')
        need(s['binary_sha256']==BINARY and s['base_binary_sha256']==BASE and s['compiled_source_sha256']==expected,'study source/binary identity')
        need(s['fixture_sha256']==FIXTURE and s['build_receipt_sha256']==d['provenance']['build_source_sha256'],'fixture/build receipt identity')
        gate=s['production_prechecks'];need(gate['binary_sha256']==BINARY and gate['select_object_sha256']==build['select_object_sha256'],'precheck provenance')
        for key in ['production_scalar_isa_matches_diagnostic','production_control_and_wide_isa_unchanged','resource_gate_passed','diagnostic_parity_passed']:need(gate[key] is True,'production precheck')
        ref=s['historical_default_output_ids'];need(len(ref)==1024,'historical ID reference')
        flags0=None;args0=None
        for r in rows:
            need(r['passed'] and r['prompt_tokens']==65536 and r['actual_outputs']==len(r['output_ids'])==1024,'64K1024 coverage')
            need(all(type(i)is int and 0<=i<248320 for i in r['output_ids']),'token domain')
            need(r['output_ids']==ref,'complete historical parity')
            need(r['prompt_reused']==0 and r['prompt_read']==65536,'full fresh prompt')
            for rate,n,ms in [('PP',65536,'prompt_ms'),('TG',1024,'decode_ms')]:
                need(math.isfinite(r[ms]) and r[ms]>0,'duration');close(r[rate],n*1000/r[ms],'native rate')
            m=study['manifests'][r['tag']];need(m['native_exit']==0 and m['fresh_process'] and m['release_binary_sha256']==BINARY and m['fixture_sha256']==FIXTURE,'fresh-process manifest')
            need(m['sampling']=={'temperature':0,'top_p':1,'top_k':1,'seed':12345},'greedy request')
            need(m['engine_info']==r['engine_info']==rows[0]['engine_info'],'within-study engine topology')
            info=r['engine_info'];need(info['context']=='204800' and info['kv_resident']=='32768' and info['expert_slots']=='19078' and info['expert_slots_primary']=='9900' and info['spec']=='6' and info['mtp_max']=='4' and info['lookup']==('3' if adaptive else '0'),'engine geometry')
            flags=dict(m['flags']);need(flags.pop('STRATA_GFX906_TOPK_FIT17')==('0' if r['tag'][0]=='A' else '1'),'treatment flag')
            need('STRATA_GFX906_TOPK_FIT17_TRACE' not in flags and 'STRATA_VERIFY_PROFILE' not in flags and 'STRATA_GFX906_ATTN_REDUCE12_TRACE' not in flags,'profiling off')
            for k,v in {'STRATA_GFX906_ATTN_REDUCE12':'1','STRATA_PRIMARY_COMMIT_OVERLAP':'1','STRATA_VERIFY_SKIP_EMPTY_PCIE':'1','STRATA_GFX906_HC_F16':'1','STRATA_GFX906_MMQ_OPT_CAP':'32'}.items():need(flags[k]==v,'retained ff34 optimization')
            if flags0 is None:flags0=flags;args0=m['full_native_args_sha256']
            need(flags==flags0 and m['full_native_args_sha256']==args0,'within-study settings isolation')
            opts=m['native_options'];need(opts['--spec']==('4' if adaptive else '6'),'requested spec')
            if adaptive:need('--suffix-draft' not in opts and '--mtp-max-t' not in opts,'original default draft args')
            else:need(opts['--suffix-draft']=='0' and opts['--mtp-max-t']=='4','fixed suffix-disabled args')
            need(opts['--layer-split']=='27' and opts['--adapt-every']=='0','fixed placement')
            if adaptive:need(r['native_done_field_count']==16 and r['optional_chain_counters_available'] is False and all(r[k] is None for k in OPTIONAL),'unavailable optional counters stay null')
            else:need(r['suffix_drafts']=={'present':False,'windows':0,'accepted':0,'offered':0},'suffix disabled')
            th=study['thermal_summary'][r['tag']];need(th['sample_count']>=20 and th['all_power_high'] and th['all_power_caps_190w'],'thermal/power coverage')
            need(all(th['max_temperature_millicelsius'][k]<v for k,v in [('temp1_input',80000),('temp2_input',90000),('temp3_input',90000)]),'observed thermal ceilings')
        decision=s['decision'];c=[counters(r,adaptive) for r in rows]
        need(decision['all1024_ids_equal'] and decision['all_counters_equal']==all(v==c[0] for v in c),'recorded counter-equality observation')
        if adaptive:
            need(s['constant_workload_claim'] is False and decision['constant_workload_claim'] is False and decision['all_topology_equal'] and s['methodological_review_approved'],'adaptive scope')
            need(s['fixed_study_summary_sha256']==d['studies']['fixed_draft']['source_sha256']['summary.json'],'fixed-study prerequisite identity')
            for idx,(ai,bi) in enumerate([(0,1),(3,2)]):
                pair=decision['paired_counter_deltas'][idx];need(pair['pair']==rows[bi]['tag']+'/'+rows[ai]['tag'],'counter pair labels')
                for key in c[ai]:
                    actual=None if c[bi][key] is None or c[ai][key] is None else c[bi][key]-c[ai][key]
                    if actual is None:need(pair['candidate_minus_control'][key] is None,'unavailable delta not zero')
                    else:close(pair['candidate_minus_control'][key],actual,'paired counter delta')
        else:need(decision['all_counters_equal'],'fixed recorded counters match')
        for key in ['PP','TG']:
            a=(rows[0][key]+rows[3][key])/2;b=(rows[1][key]+rows[2][key])/2;x=decision[key]
            close(x['control_mean'],a,'control mean');close(x['candidate_mean'],b,'candidate mean');close(x['gain_pct'],100*(b/a-1),'mean rate gain')
            need(len(x['paired_gain_pct'])==2,'two pair gains')
            for saved,ai,bi in zip(x['paired_gain_pct'],[0,3],[1,2]):close(saved,100*(rows[bi][key]/rows[ai][key]-1),'paired rate gain')
        need(decision['passes_cost_gate'] and decision['TG']['gain_pct']>=1 and min(decision['TG']['paired_gain_pct'])>0 and decision['PP']['gain_pct']>=-1,'decode cost gate')
        need(all(digest(v) for v in study['source_sha256'].values()),'source hash format')
        outputs[name]=ref;report[name]={'TG_gain_pct':decision['TG']['gain_pct'],'PP_gain_pct':decision['PP']['gain_pct']}
    need(outputs['fixed_draft']==outputs['adaptive_default'],'common historical IDs')
    fail=d['preserved_failures'];need(fail['component_30_percent_screen']['status']=='FAIL retained' and not fail['component_30_percent_screen']['model_gain_claim'],'original component failure')
    f=fail['historical_counter_gate'];old=f['source_receipt']['summary'];need(not old['benchmark_passed'] and len(old['results'])==1 and old['results'][0]['tag']=='A1' and f['historical_ids_exact'],'historical workload gate failure retained')
    need(old['results'][0]['output_ids']==old['reference_output_ids'],'failed A1 quality still exact')
    need(f['source_receipt']['manifests']['A1']['flags']['STRATA_GFX906_TOPK_FIT17']=='0','failed historical A1 was control')
    need(f['observed_counters']!=f['historical_expected_counters'],'historical counters differ')
    for k in CORE:need(f['observed_minus_historical'][k]==f['observed_counters'][k]-f['historical_expected_counters'][k],'historical counter delta')
    parser=fail['native_parser_attempt'];need(parser['expected_in_incorrect_parser']==21 and parser['actual_default_protocol_fields']==16 and parser['numeric_results_available'] is False,'distinct parser failure retained')
    qualification=d['correctness'];qs=qualification['summary'];refs=qualification['references']
    need(qs['qualification_passed'] and qs['owned_containers_cleaned'] and not qs['api_touched'] and not qs['promoted'] and not qs['performance_comparison'],'correctness-only completion/scope')
    need(qs['binary_sha256']==BINARY and qs['base_binary_sha256']==BASE and qs['compiled_source_sha256']==expected,'correctness provenance')
    reference_hash=hashlib.sha256((json.dumps(refs,indent=2)+'\n').encode()).hexdigest()
    need(reference_hash==qs['reference_sha256']=='13b8fd8b67d24cc65a027c990281f8d19696d0b77a72a75316638a438737fb9d','complete correctness reference binding')
    need(qs['reference_source_sha256']==refs['source_sha256'] and refs['binary_sha256']==BASE,'ff34 reference provenance')
    need([(r['prompt_tokens'],r['actual_outputs']) for r in qs['results']]==[(4096,1024),(200000,256)],'4K/200K coverage')
    for r in qs['results']:
        ref=refs['results'][str(r['prompt_tokens'])];need(r['output_ids']==ref['output_ids'] and r['actual_outputs']==len(r['output_ids']) and r['all_reference_ids_equal'],'correctness exact IDs')
        need(r['engine_info']==ref['engine_info'],'correctness topology')
        for rate,n,ms in [('PP',r['prompt_tokens'],'prompt_ms'),('TG',r['actual_outputs'],'decode_ms')]:close(r[rate],n*1000/r[ms],'diagnostic native rate')
        m=qualification['manifests'][r['tag']];need(m['native_exit']==0 and m['release_binary_sha256']==BINARY and m['flags']['STRATA_GFX906_TOPK_FIT17']=='1' and m['flags']['STRATA_GFX906_TOPK_FIT17_TRACE']=='1','correctness opt-in/trace')
        need(r['native_done_field_count']==16 and all(r[k] is None for k in OPTIONAL),'correctness optional null counters')
        need(len(r['fit17_host_topology'])>=1 and all(1<=x['nq']<=8 and x['capacity_blocks']>=17408 for x in r['fit17_host_topology']),'host launch topology only')
        f=r['fallback_source_inference'];need(f['inferred_not_instrumented'] is True and f['runtime_branch_counter_available'] is False and f['source_sha256']==SELECT,'honest fallback evidence')
        low=r['prompt_tokens']-1;high=r['prompt_tokens']+r['actual_outputs']+8
        need(f['conservative_n_kv_bounds']==[low,high] and f['max_bid_plus_one_bounds']==[low//4+1,high//4+1],'fallback bound arithmetic')
        owner='guarded-reference256' if high<=24576 else 'guarded-register66-wide'
        need(f['expected_decode_owner']==owner and (high<=24576 or low//4+1>17408),'fallback guard inference')
    return {'passed':True,'studies':report,'scope':'offline arithmetic/parity/provenance/claims checks only'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('receipt',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args();d=json.loads(a.receipt.read_text());result=validate(d)
    if a.selftest:
        cases=[lambda x:x['studies']['fixed_draft']['summary']['results'][1]['output_ids'].__setitem__(900,-1),lambda x:x['studies']['adaptive_default']['summary']['results'][2].__setitem__('TG',1),lambda x:x['studies']['fixed_draft']['summary']['decision']['TG'].__setitem__('gain_pct',99),lambda x:x['studies']['adaptive_default']['summary']['decision']['paired_counter_deltas'][1]['candidate_minus_control'].__setitem__('offered',0),lambda x:x['studies']['adaptive_default']['summary']['results'][0].__setitem__('lookup_chain_offered',0),lambda x:x['studies']['adaptive_default']['summary']['decision'].__setitem__('constant_workload_claim',True),lambda x:x['studies']['fixed_draft']['summary']['results'][1].__setitem__('offered',0),lambda x:x['studies']['fixed_draft']['manifests']['A1']['flags'].__setitem__('STRATA_GFX906_ATTN_REDUCE12','0'),lambda x:x['studies']['adaptive_default']['summary'].__setitem__('fixed_study_summary_sha256','0'*64),lambda x:x['provenance']['build'].__setitem__('sources_restored',False),lambda x:x['provenance']['micro']['budget']['initial_gpu0'].__setitem__('first_gpu_gate_passed',True),lambda x:x['preserved_failures']['historical_counter_gate']['source_receipt']['summary'].__setitem__('benchmark_passed',True),lambda x:x['preserved_failures']['native_parser_attempt'].__setitem__('actual_default_protocol_fields',21),lambda x:x['studies']['adaptive_default']['thermal_summary']['B2']['max_temperature_millicelsius'].__setitem__('temp2_input',95000),lambda x:x['studies']['fixed_draft']['summary'].__setitem__('api_touched',True)]
        cases += [lambda x:x['correctness']['summary']['results'][1]['output_ids'].__setitem__(100,-1),lambda x:x['correctness']['summary'].__setitem__('performance_comparison',True),lambda x:x['correctness']['summary']['results'][1]['fallback_source_inference'].__setitem__('inferred_not_instrumented',False)]
        for change in cases:
            bad=copy.deepcopy(d);change(bad)
            try:validate(bad)
            except (ValueError,KeyError,TypeError):pass
            else:raise RuntimeError('missed corruption')
        result['negative_cases_rejected']=len(cases)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
