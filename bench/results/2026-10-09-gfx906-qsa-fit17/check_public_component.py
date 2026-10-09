#!/usr/bin/env python3
"""Validate sanitized public-selector receipts; no build or GPU execution."""
import argparse
import copy
import json
import math
import statistics
from pathlib import Path

def need(x,why):
    if not x:raise ValueError(why)
def close(a,b,why):need(math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12),why)
def digest(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)
def validate(d):
    need(d['exit_code']==0 and d['qualification_completed'] is True and d['all_correctness_passed'] is True,'completion')
    need(d['original_discovery_gate_redefined'] is False,'original gate retained')
    need(d['pre_gpu_gate_sha256']=='ca533b7989188330c903055c4ebc79d4006ca1922803ba2f9aba7f25ee2163d4','gate binding')
    b=d['build_and_isa'];need(b['passed'] is True and b['resource_isa_passed'] is True and b['support_archive_used'] is False,'direct component build')
    need(b['public_commit']=='ca3533157d066a13b128f3daa61f56411dcf3155','public base')
    need(b['source_sha256']['candidate']=='5fc5d78c6155fa0987dee751a875ab714516c88209b0938db17699061cc7de1a','public source')
    need(b['private_model_binary_sha256']=='c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049','private ISA comparison identity')
    for k in ['direct_scalar_wide_control_counted_reference_instruction_equivalence','default_off_control_counted_reference_equal_public_base','all_selector_resource_abi_metadata_equal_private_production']:need(b[k] is True,'direct ISA equivalence')
    for name,scratch,spg,spv in [('scalar17',56,44,25),('wide66',1048,539,468),('old66',1048,527,467)]:
        r=b['resources'][name];need(r=={'sgpr':104,'vgpr':64,'scratch_bytes_per_lane':scratch,'sgpr_spills':spg,'vgpr_spills':spv,'lds_bytes_per_block':32908,'occupancy_waves_per_simd':4},'honest resources')
    rows=d['correctness'];timing=d['timing'];need(len(rows)==46 and len(timing)==8,'process coverage')
    for r in rows+timing:
        need(r['native_exit']==0 and r['device'] in [0,1],'exit/device')
        need(r['binary_sha256']==b['binaries'][r['binary']],'binary binding')
        need(digest(r['stdout_sha256']) and digest(r['stderr_sha256']),'evidence hashes')
    need(len({r['tag'] for r in rows+timing})==54,'unique process tags')
    selftests=[r for r in rows if r['tag'].startswith('public-')];trans=[r for r in rows if r['tag'].startswith('trans-')];capture=[r for r in rows if r['tag'].startswith('capture-')]
    for gpu in [0,1]:
        for group,binary in [(selftests,'public-parity'),(capture,'capture')]:
            got={(r['binary'],r['mode']) for r in group if r['device']==gpu}
            need(got=={(binary+'.base',None),(binary+'.fit17',None),(binary+'.fit17',0),(binary+'.fit17',1)},'unset/off/on coverage')
        got={(r['binary'],r['mode'],r['nq']) for r in trans if r['device']==gpu}
        need(got=={(bin,mode,nq) for bin,mode in [('transition.base',0),('transition.fit17',0),('transition.fit17',1)] for nq in [1,4,6,8,9]},'transition mode/geometry coverage')
    for r in selftests:
        need(r['selftest_cases']==r['parsed_selftest_cases']==18 and r['terminal_pass'] is True and r['parity_passed'] is True and r['timing_claim'] is False,'selftest parity')
    for r in trans:
        need(r['cases']==r['parsed_cases']==r['case_pass_lines']==(23 if r['nq']==1 else 29),'transition cases')
        need(r['graph_instantiations']==r['constant_addresses']==r['constant_capacities']==1 and r['parity_passed'] is True and r['timing_claim'] is False,'graph parity')
    for r in capture+timing:
        need(r['captured_reference_parity'] and r['graph_ids_passed'] and r['input_bytes_unchanged'] and r['all_parity_passed'],'captured parity')
        g=r['geometry'];need(g['nq']==4 and g['pos0']==65536 and g['cap']==2051 and g['capacity_blocks']==51202 and g['captured_device']==g['replay_device']==r['device'],'capture geometry')
    counts={'processes':len(rows)+len(timing),'correctness_processes':len(rows),'timing_processes':len(timing),'selftest_processes':len(selftests),'selftest_cases':sum(r['selftest_cases'] for r in selftests),'transition_processes':len(trans),'transition_windows':sum(r['cases'] for r in trans),'transition_rows':sum(r['cases']*r['nq'] for r in trans),'capture_correctness_processes':len(capture)}
    need(counts==d['counts']=={'processes':54,'correctness_processes':46,'timing_processes':8,'selftest_processes':8,'selftest_cases':144,'transition_processes':30,'transition_windows':834,'transition_rows':4836,'capture_correctness_processes':8},'recomputed counts')
    need(len(d['component'])==2 and [r['device'] for r in d['component']]==[0,1],'component coverage')
    gains=[]
    for gpu in [0,1]:
        tt=[r for r in timing if r['device']==gpu];need([r['tag'] for r in tt]==[f'abba-g{gpu}-{tag}' for tag in ['A1','B1','B2','A2']],'ABBA order')
        need([r['mode'] for r in tt]==[0,1,1,0],'treatment')
        for r in tt:
            need(r['binary']=='capture.fit17' and r['trace_enabled'] is False and r['stderr_bytes']==0,'matched binary/untraced timing')
            need(r['geometry']['batch']==64 and r['geometry']['samples']==len(r['samples_ms'])==7,'timing repetitions')
            need(all(math.isfinite(v) and v>0 for v in r['samples_ms']),'finite samples');close(statistics.median(r['samples_ms']),r['median_ms_per_call'],'median')
        x=d['component'][gpu];aa=[tt[0]['median_ms_per_call'],tt[3]['median_ms_per_call']];bb=[tt[1]['median_ms_per_call'],tt[2]['median_ms_per_call']]
        need(x['A_run_medians']==aa and x['B_run_medians']==bb,'arm binding');a=statistics.mean(aa);b=statistics.mean(bb)
        close(a,x['A_ms'],'A mean');close(b,x['B_ms'],'B mean');g=100*(a-b)/a;close(g,x['latency_reduction_pct'],'latency arithmetic');gains.append(g)
        need(max(bb)<min(aa) and x['all_B_faster_than_all_A'] is True,'both pairs positive')
        need(x['status']=='public_reproduction_measurement','reproduction scope')
    need(d['component'][0]['engineering_gate_pct']==30 and d['component'][0]['original_30pct_discovery_gate_passed'] is False and gains[0]<30,'30 percent failure retained')
    need(d['public_both_pairs_positive'] is True,'pair summary')
    return {'passed':True,'processes':54,'latency_reduction_pct':gains,'scope':'offline sanitized receipt consistency only'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('receipt',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args();d=json.loads(a.receipt.read_text());out=validate(d)
    if a.selftest:
        mutations=[lambda x:x.__setitem__('exit_code',1),lambda x:x['correctness'].pop(),lambda x:x['counts'].__setitem__('transition_rows',1),lambda x:x['correctness'][0].__setitem__('parity_passed',False),lambda x:x['correctness'][8].__setitem__('graph_instantiations',2),lambda x:x['correctness'][8].__setitem__('case_pass_lines',0),lambda x:x['timing'][0]['samples_ms'].__setitem__(3,99),lambda x:x['timing'][1].__setitem__('mode',0),lambda x:x['timing'][0].__setitem__('trace_enabled',True),lambda x:x['component'][0].__setitem__('latency_reduction_pct',99),lambda x:x.__setitem__('original_discovery_gate_redefined',True),lambda x:x['build_and_isa'].__setitem__('support_archive_used',True),lambda x:x['build_and_isa']['source_sha256'].__setitem__('candidate','0'*64),lambda x:x['build_and_isa']['resources']['scalar17'].__setitem__('scratch_bytes_per_lane',0),lambda x:x['build_and_isa'].__setitem__('direct_scalar_wide_control_counted_reference_instruction_equivalence',False),lambda x:x['timing'][0].__setitem__('binary_sha256','0'*64)]
        for m in mutations:
            bad=copy.deepcopy(d);m(bad)
            try:validate(bad)
            except (ValueError,KeyError,TypeError):pass
            else:raise RuntimeError('missed corruption')
        out['negative_cases_rejected']=len(mutations)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
