#!/usr/bin/env python3
"""Source-confirmed protocol: main 477ac13, generate.cpp lines 11621-11705 and 14605-14631.
Input: JSON list of 12 objects {pair: 1..6, arm: A|B, stdout: path,
exit_code: 0}. Paths relative to manifest. Raw logs remain source of truth.
Host lifecycle, startup config/device and stderr gates are root's responsibility.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import statistics as st
import sys

ORDER = ['AB', 'BA', 'BA', 'AB', 'AB', 'BA']
FIELDS = ('record produced_n prompt_n prompt_ms decode_ms finish draft_accepted '
          'draft_offered resume req_hits req_look ram_reads_delta '
          'file_reads_delta file_read_MB read_n req_offload').split()

def need(ok, message):
    if not ok:
        raise ValueError(message)

def parse(text, *, prompt_count=65536, output_count=1024, ignore_info_fields=('vram_free_mib','engine')):
    need(type(prompt_count) is int and prompt_count>0 and type(output_count) is int and output_count>0, 'invalid explicit work dimensions')
    lines = text.splitlines()
    need(not any(re.match(r'^\s*(ERR|FATAL|FAIL)\b', x) for x in lines), 'error in stdout')
    ready = [x for x in lines if x.startswith('READY ')]
    need(len(ready) == 1, 'expected one READY')
    tr = [x for x in lines if re.match(r'^\s*T(?:\s|$)', x)]
    need(all(re.fullmatch(r'T [0-9]+', x) for x in tr), 'malformed token')
    tokens = [int(x[2:]) for x in tr]
    done = [x for x in lines if re.match(r'^\s*DONE(?:\s|$)', x)]
    need(len(done) == 1, 'expected one DONE')
    f = done[0].split()
    need(len(f) == len(FIELDS)+2, 'expected no-lookup-chain DONE schema')
    need(re.fullmatch(r'chunk=[0-9]+', f[16]) is not None and re.fullmatch(r'experts_streamed=[0-9]+', f[17]) is not None, 'DONE work suffix changed')
    need(len(tokens) == int(f[1]) == output_count and int(f[2]) == int(f[14]) == prompt_count, 'work mismatch')
    need(f[5] == 'length' and int(f[8]) == 0, 'finish/cache mismatch')
    need(all(re.fullmatch(r'[0-9]+',f[i]) for i in (1,2,6,7,8,9,10,11,12,14,15)), 'invalid DONE counter')
    need(math.isfinite(float(f[13])) and float(f[13])>=0, 'invalid file MB counter')
    p, g = float(f[3]), float(f[4])
    need(all(math.isfinite(v) and v > 0 for v in (p, g)), 'invalid time')
    positions = [i for i,x in enumerate(lines) if re.fullmatch(r'T [0-9]+', x)]
    need(lines.index(ready[0]) < min(positions) <= max(positions) < lines.index(done[0]), 'ordering')
    need(not any(x.strip() for x in lines[lines.index(done[0])+1:]), 'output after DONE')
    counters = {k:f[i] for i,k in enumerate(FIELDS) if i not in (0,3,4)}
    counters.update(dict(x.split('=',1) for x in f[16:]))
    resume = [x for x in lines if x.startswith('RESUME ')]
    reused = [x for x in lines if x.startswith('REUSED ')]
    need(resume == ['RESUME 0'] and reused == ['REUSED 0'], 'cold prompt required')
    pp = [x.split() for x in lines if x.startswith('PP ')]
    need(bool(pp) and all(len(x)==5 and int(x[2])==prompt_count and all(math.isfinite(float(t)) and float(t)>=0 for t in x[3:]) for x in pp), 'invalid PP progress')
    counts = [int(x[1]) for x in pp]
    need(all(0<a<=prompt_count for a in counts) and counts==sorted(set(counts)), 'invalid PP positions')
    counters['pp_positions'] = counts
    pp_indices=[i for i,x in enumerate(lines) if x.startswith('PP ')]
    need(lines.index(ready[0]) < lines.index(resume[0]) < min(pp_indices) <= max(pp_indices) < lines.index(reused[0]) < min(positions), 'cold prompt chronology differs')
    info_lines = [x for x in lines if x.startswith('INFO ')]
    need(len(info_lines)==1, 'expected one INFO')
    need(lines.index(info_lines[0])<lines.index(ready[0]), 'INFO must precede READY')
    pieces=info_lines[0].split()[1:]
    need(all('=' in x for x in pieces), 'malformed INFO')
    info=dict(x.split('=',1) for x in pieces)
    need(len(info)==len(pieces), 'duplicate INFO key')
    need(ready[0]=='READY 262144 stop', 'READY context differs')
    for key in ignore_info_fields: info.pop(key,None)
    return dict(info=info, output_ids=tokens, prompt_ms=p, decode_ms=g, total_ms=p+g,
                token_sha256=hashlib.sha256(json.dumps(tokens, separators=(',',':')).encode()).hexdigest(),
                counters=counters)

def summary(rows):
    need(len(rows) == 12, 'six complete pairs required')
    wanted = [(i, a) for i, order in enumerate(ORDER, 1) for a in order]
    need([(r['pair'],r['arm']) for r in rows] == wanted, 'run order differs from preregistered plan')
    need(all(r['counters']['prompt_n']=='65536' and r['counters']['read_n']=='65536' and r['counters']['produced_n']=='1024' for r in rows), 'performance summary requires fixed 65536/1024 workload')
    ref = rows[0]
    need(all(r['output_ids'] == ref['output_ids'] and r['token_sha256'] == ref['token_sha256'] and r['counters'] == ref['counters'] and r['info'] == ref['info'] for r in rows),
         'output/work parity failed; no performance score')
    out = {}
    for metric,key,n in [('PP','prompt_ms',65536),('TG','decode_ms',1024),('combined_latency','total_ms',None)]:
        pairs = []
        for i in range(1,7):
            arm = {r['arm']:r for r in rows if r['pair'] == i}
            ratio = arm['A'][key]/arm['B'][key]
            pairs.append(dict(pair=i, A_ms=arm['A'][key], B_ms=arm['B'][key], B_over_A_speedup=ratio, gain_pct=100*(ratio-1)))
        logs = [math.log(p['B_over_A_speedup']) for p in pairs]
        mean, sd = st.mean(logs), st.stdev(logs)
        half = 2.570581835636305*sd/math.sqrt(6)  # Student t, df=5, two-sided 95%
        result = dict(pairs=pairs, paired_geomean_gain_pct=100*math.expm1(mean),
                      paired_log_sd=sd, approximate_95pct_gain_CI=[100*math.expm1(mean-half),100*math.expm1(mean+half)],
                      pair_gain_range_pct=[min(p['gain_pct'] for p in pairs),max(p['gain_pct'] for p in pairs)])
        sums = {a:sum(r[key] for r in rows if r['arm']==a) for a in 'AB'}
        result['pooled_speedup_ratio'] = sums['A']/sums['B']
        if n:
            result['pooled_tokens_per_s'] = {a:6*n*1000/sums[a] for a in 'AB'}
        out[metric] = result
    return dict(scope='timing summary only; root must also pass startup/config/device/stderr/component gates',
                parity=True, rows=rows, metrics=out)

if __name__ == '__main__':
    manifest = Path(sys.argv[1])
    records = json.loads(manifest.read_text())
    rows = []
    for rec in records:
        need(rec['exit_code'] == 0, 'unsuccessful exit')
        row = parse((manifest.parent / rec['stdout']).read_text())
        rows.append(dict(pair=rec['pair'], arm=rec['arm'], **row))
    print(json.dumps(summary(rows), indent=2))
