#!/usr/bin/env python3
"""Excluded full-profile qualification only: fresh A/B, 65536 + 1024 tokens.
Uses the reviewed lifecycle; never calls performance summary or computes TPS.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import uuid
from protocol import need
from run_pairs import PROMPT_SHA, measure, save

PROMPT_COUNT=65536
OUTPUT_COUNT=1024

def main():
    ap=argparse.ArgumentParser();ap.add_argument('config');ap.add_argument('output');a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text())
    need(cfg.get('protocol_source_commit')=='477ac13cbe8e582c20484871ce459d20d82df09d','source pin missing')
    need('STRATA_API_KEY' not in cfg['environment'] and all('STRATA_API_KEY' not in e for e in cfg.get('treatment_environment',{}).values()),'API credential forbidden in config')
    need(cfg.get('expected_info') and cfg.get('required_stderr_fragments'),'fresh startup checks required')
    need(cfg['image'].startswith('sha256:'),'pinned image required')
    need('--lookup-chain' not in cfg['args'],'lookup-chain outside this protocol')
    need(str(cfg['environment'].get('STRATA_ROUTE_TAIL_SKIP'))=='0','canary requires explicit full-routed-work common profile')
    need(all('STRATA_ROUTE_TAIL_SKIP' not in e for e in cfg.get('treatment_environment',{}).values()),'route-tail profile may not differ between arms')
    data=Path(cfg['prompt']).read_bytes()
    need(hashlib.sha256(data).hexdigest()==PROMPT_SHA,'frozen full prompt SHA mismatch')
    full=json.loads(data)
    need(len(full)==65536 and all(type(x) is int and x>=0 for x in full),'invalid frozen full prompt')
    ids=full[:PROMPT_COUNT]
    cfg=copy.deepcopy(cfg)
    owner=uuid.uuid4().hex
    with open(cfg['lock_path'],'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
        save(out/'config.json',cfg)
        state=dict(owner=owner,pid=os.getpid(),state='running',scope='excluded_full_profile_canary',order=['A','B'],
                   prompt_count=PROMPT_COUNT,output_count=OUTPUT_COUNT,full_prompt_sha256=PROMPT_SHA,
                   prompt_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),
                   ignored_info_fields=['vram_free_mib'],rows=[],performance_qualified=False,quality_claim=False)
        save(out/'status.json',state)
        try:
            for arm in state['order']:
                tag='canary-'+arm
                row=measure(cfg,arm,tag,out,owner,ids,dict(pair=0,arm=arm,scope='excluded_full_profile_canary'),
                            prompt_count=PROMPT_COUNT,output_count=OUTPUT_COUNT,ignore_info_fields=('vram_free_mib',))
                if state['rows']:
                    ref=state['rows'][0]
                    if not all(row[k]==ref[k] for k in ('output_ids','token_sha256','counters','info')):
                        path=out/(tag+'.receipt.json');receipt=json.loads(path.read_text())
                        receipt.update(state='rejected',error='full-profile canary output/work/layout parity mismatch');save(path,receipt)
                        raise ValueError('strict full-profile canary parity mismatch in '+arm)
                # Native raw/receipt timings remain auditable; no speed claim is calculated.
                row={k:v for k,v in row.items() if k not in ('prompt_ms','decode_ms','total_ms')}
                state['rows'].append(row);save(out/'status.json',state)
                print(json.dumps(dict(arm=arm,state='parity_pass',output_tokens=OUTPUT_COUNT)),flush=True)
            state.update(state='complete',full_profile_canary_passed=True)
        except BaseException as exc:
            state.update(state='failed',full_profile_canary_passed=False,error=repr(exc));raise
        finally:save(out/'status.json',state)

if __name__=='__main__':main()
