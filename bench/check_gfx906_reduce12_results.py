#!/usr/bin/env python3
"""Offline receipt consistency check; never runs a GPU, model or API test."""
import argparse
import copy
import json
import math
from pathlib import Path

def need(ok, why):
    if not ok:
        raise ValueError(why)

def close(x, y, why):
    need(math.isfinite(x) and math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-10), why)

def validate(d):
    m = d['model']['results']; q = d['qualification']['results']; ref = d['archived_200k_reference']['result']
    need([r['tag'] for r in m] == ['A1','B1','B2','A2'], 'ABBA order')
    for r in m + q + [ref, d['smoke']]:
        ids = r['output_ids']
        need(r['passed'] is True and len(ids) == r['actual_outputs'], 'output completion/count')
        need(all(type(i) is int and 0 <= i < 248320 for i in ids), 'ID domain')
        for rate, count, duration in [('PP',r['prompt_tokens'],'prompt_ms'),('TG',len(ids),'decode_ms')]:
            need(math.isfinite(r[duration]) and r[duration] > 0, 'positive finite duration')
            close(r[rate], count*1000/r[duration], 'rate arithmetic')
        need(r['kv'] == 'int8' and r['sampling'] == {'temperature':0,'top_p':1,'top_k':1,'seed':12345}, 'fixed input mode')
    need(all(r['prompt_tokens']==65536 and r['actual_outputs']==1024 for r in m),'64K coverage')
    need(all(r['output_ids']==m[0]['output_ids'] for r in m),'full 64K ID parity')
    need(all(r['engine_info']==m[0]['engine_info'] for r in m),'fixed engine configuration')
    for key in ['accepted','offered','cache_hits','lookups','prompt_read','prompt_reused']:
        need(len({r[key] for r in m})==1, 'matched counters')
    for key in ['PP','TG']:
        a=(m[0][key]+m[3][key])/2; b=(m[1][key]+m[2][key])/2; gain=100*(b/a-1)
        pairs=[100*(m[bi][key]/m[ai][key]-1) for ai,bi in [(0,1),(3,2)]]
        close(gain,d['model']['decision'][key+'_gain_pct'],'decision gain')
        close(gain,d['recomputed_model'][key]['gain_pct'],'receipt gain')
        close(a,d['recomputed_model'][key]['control_mean'],'control mean')
        close(b,d['recomputed_model'][key]['candidate_mean'],'candidate mean')
        for actual,saved in zip(pairs,d['recomputed_model'][key]['paired_gain_pct']):close(actual,saved,'paired gain')
        need(min(pairs)>0,'positive pairs')
        need(gain >= (1 if key=='PP' else -1),'model cost gate')
    manifests=d['model_manifests']; need([r['tag'] for r in manifests]==['A1','B1','B2','A2'],'manifest coverage')
    baseline=None
    for r in manifests:
        need(r['binary_sha256']==d['build']['binary_sha256']==d['release']['binary_sha256'],'binary identity')
        need(r['native_exit']==0 and not r['prompt_reuse'] and r['adapt_every']==0,'native completion/control')
        flags=r['flags'].copy(); need(flags.pop('STRATA_GFX906_ATTN_REDUCE12')==('0' if r['tag'].startswith('A') else '1'),'treatment flag')
        need(flags.get('STRATA_GFX906_ATTN_REDUCE12_TRACE','0')!='1' and not r['reduce12_trace_present'],'trace absent from performance arms')
        for k,v in {'STRATA_PRIMARY_COMMIT_OVERLAP':'1','STRATA_VERIFY_SKIP_EMPTY_PCIE':'1','STRATA_GFX906_HC_F16':'1','STRATA_GFX906_MMQ_OPT_CAP':'32','STRATA_GFX906_ATTN_QUERY_SWIZZLE':'1','STRATA_ATTN_LANECELL':'0'}.items():need(flags.get(k)==v,'retained optimization')
        current=(flags,r['source_epoch'],r['model_revision'],r['layer_split'],r['resident_kv_tokens'],r['mtp_window'])
        if baseline is None:baseline=current
        need(current==baseline,'only reduce12 flag changes')
    q4=[r for r in q if r['prompt_tokens']==4096]; q200=[r for r in q if r['prompt_tokens']==200000]
    need(len(q4)==2 and all(r['actual_outputs']==1024 for r in q4),'4K coverage')
    need(q4[0]['output_ids']==q4[1]['output_ids'],'4K parity')
    for key in ['PP','TG']:close(100*(q4[0][key]/q4[1][key]-1),d['qualification']['decision']['4k'][key+'_gain_pct'],'4K rate gain')
    need(len(q200)==1 and q200[0]['actual_outputs']==ref['actual_outputs']==256 and ref['prompt_tokens']==200000,'200K coverage')
    need(q200[0]['output_ids']==ref['output_ids'],'archived full 200K parity')
    need(d['qualification']['decision']['200k']['fresh_performance_comparison'] is False,'200K scope')
    need(d['smoke']['actual_outputs']==32 and d['smoke']['output_ids']==q4[0]['output_ids'][:32],'smoke ID parity')
    need(d['build']['exit_code']==0 and d['build']['sources_restored'],'build completion')
    isa=d['production_isa']
    for arm,vgpr,shuffles in [('A',42,70),('B',48,26)]:
        r=isa[arm];need(r['.vgpr_count']==vgpr and r['shuffles']==shuffles and r['v_fmac_f32']==87 and r['.group_segment_fixed_size']==15872 and r['.private_segment_fixed_size']==0,'production ISA resources')
    api=d['api'];need(api['passed'] and api['original_configuration_restored'] and api['temporary_only'],'API restoration')
    need(all(api[k]=='passed' for k in ['tools','vision','parking','cancel']),'API checks')
    need(api['candidate_binary_sha256']==d['build']['binary_sha256'],'API binary identity')
    c=api['disconnect_test'];need(c['passed'] and c['same_engine_process'] and c['cancel_finish']=='disconnect' and c['post_cancel_response']=='42','cancel recovery')
    need(c['stream_chunks_before_disconnect']==12 and c['cancel_output_tokens']==14,'cancel counts')
    v=api['verification_evidence']
    need(v['auth']=={'unauthenticated_models':401,'ui':404},'auth/UI status')
    need(v['vision_trials']==2,'vision trial coverage')
    need(v['cancel']==c,'cancel evidence consistency')
    restoration=v['configuration_restoration']
    for prefix in ['config','compose']:
        need(restoration[prefix+'_bytes_equal'] is True,'restoration byte equality')
        before=restoration[prefix+'_before_sha256']; after=restoration[prefix+'_after_sha256']
        need(before==after and len(before)==64 and all(ch in '0123456789abcdef' for ch in before),'restoration SHA256 equality')
    need(v['helper_sha256']['cancel']==d['evidence']['source_review']['cancel_helper']['sha256'],'reviewed cancel helper identity')
    need(not d['release']['promoted'] and not d['source_port']['compiled_separately'] and not d['source_port']['pushed'],'release/port status')
    return {'passed':True,'PP_gain_pct':d['recomputed_model']['PP']['gain_pct'],'TG_gain_pct':d['recomputed_model']['TG']['gain_pct'],'scope':'offline receipt consistency only'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args();d=json.loads(a.results.read_text());out=validate(d)
    if a.selftest:
        mutations=[('64K token',lambda x:x['model']['results'][1]['output_ids'].__setitem__(900,0)),('truncated IDs',lambda x:x['model']['results'][2]['output_ids'].pop()),('rate',lambda x:x['model']['results'][0].__setitem__('PP',1)),('gain',lambda x:x['recomputed_model']['PP'].__setitem__('gain_pct',99)),('reference token',lambda x:x['archived_200k_reference']['result']['output_ids'].__setitem__(200,0)),('retained flag',lambda x:x['model_manifests'][1]['flags'].__setitem__('STRATA_PRIMARY_COMMIT_OVERLAP','0')),('trace',lambda x:x['model_manifests'][0]['flags'].__setitem__('STRATA_GFX906_ATTN_REDUCE12_TRACE','1')),('ISA',lambda x:x['production_isa']['B'].__setitem__('.private_segment_fixed_size',4)),('cancel',lambda x:x['api']['disconnect_test'].__setitem__('same_engine_process',False)),('restore',lambda x:x['api'].__setitem__('original_configuration_restored',False))]
        mutations += [
            ('auth',lambda x:x['api']['verification_evidence']['auth'].__setitem__('unauthenticated_models',200)),
            ('vision',lambda x:x['api']['verification_evidence'].__setitem__('vision_trials',0)),
            ('config hash',lambda x:x['api']['verification_evidence']['configuration_restoration'].__setitem__('config_after_sha256','0'*64)),
            ('compose equality',lambda x:x['api']['verification_evidence']['configuration_restoration'].__setitem__('compose_bytes_equal',False)),
            ('helper identity',lambda x:x['api']['verification_evidence']['helper_sha256'].__setitem__('cancel','0'*64)),
        ]
        for name,mutate in mutations:
            bad=copy.deepcopy(d);mutate(bad)
            try:validate(bad)
            except (ValueError,KeyError,TypeError):pass
            else:raise ValueError('missed corruption: '+name)
        out['negative_cases_rejected']=len(mutations)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
