#!/usr/bin/env python3
"""Recheck archived numbers and IDs; this does not execute GPU or API tests."""
import argparse
import copy
import json
import math
from pathlib import Path


def need(ok, why):
    if not ok:
        raise ValueError(why)


def validate(d):
    model = d['model']['results']
    q = d['qualification']['results']
    need([r['tag'] for r in model] == ['A1', 'B1', 'B2', 'A2'], 'ABBA ordering')
    for r in model + q:
        ids = r['output_ids']
        need(r['passed'] and len(ids) == r['actual_outputs'], 'completed output count')
        need(all(type(i) is int and 0 <= i < 248320 for i in ids), 'token IDs')
        for key, count, mskey in [('PP', r['prompt_tokens'], 'prompt_ms'), ('TG', len(ids), 'decode_ms')]:
            ms = r[mskey]
            need(math.isfinite(ms) and ms > 0, 'duration')
            need(math.isclose(r[key], count * 1000 / ms, rel_tol=1e-10), 'rate arithmetic')
        info = r['engine_info']
        need(int(info['expert_slots']) == 19078 and int(info['expert_slots_primary']) == 9900, 'fixed expert slots')
        need(int(info['context']) == 204800 and int(info['kv_resident']) == 32768, 'capacity')
    need(all(r['prompt_tokens'] == 65536 and r['actual_outputs'] == 1024 for r in model), '64K coverage')
    need(all(r['output_ids'] == model[0]['output_ids'] for r in model), '64K parity')
    a, b = [model[0], model[3]], [model[1], model[2]]
    gain = 100 * (sum(r['TG'] for r in b) / sum(r['TG'] for r in a) - 1)
    pairs = [100 * (y['TG'] / x['TG'] - 1) for x, y in zip(a, b)]
    need(gain >= 1 and min(pairs) > 0, 'performance screen')
    need(math.isclose(gain, d['model']['decision']['TG_gain_pct'], abs_tol=1e-10), 'reported gain')
    q4 = [r for r in q if r['prompt_tokens'] == 4096]
    q200 = [r for r in q if r['prompt_tokens'] == 200000]
    need(len(q4) == 2 and all(r['actual_outputs'] == 1024 for r in q4), '4K coverage')
    need(q4[0]['output_ids'] == q4[1]['output_ids'], '4K parity')
    need(len(q200) == 1 and q200[0]['actual_outputs'] == 256, '200K coverage')
    need(q200[0]['output_ids'] == d['archived_200k_reference']['result']['output_ids'], 'archived 200K parity')
    smoke = d['smoke']['results']
    need(len(smoke) == 3 and all(r['passed'] for r in smoke), 'smoke modes')
    for r in smoke:
        need([len(x['output_ids']) for x in r['requests']] == [32, 1], 'smoke lengths')
        need([x['output_ids'] for x in r['requests']] == [x['output_ids'] for x in smoke[0]['requests']], 'smoke parity')
    api = d['api']
    need(api['passed'] and api['original_configuration_restored'], 'API restoration')
    need(all(api[k] == 'passed' for k in ['tools', 'vision', 'parking', 'cancel']), 'API coverage')
    c = api['disconnect_test']
    need(c['passed'] and c['same_engine_process'] and c['cancel_finish'] in ('disconnect', 'cancel'), 'disconnect recovery')
    need('42' in c['post_cancel_response'], 'post-disconnect response')
    return {'passed': True, 'TG_gain_pct': gain, 'paired_TG_gains_pct': pairs, 'scope': 'receipt validation only'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('results', type=Path)
    p.add_argument('--selftest', action='store_true')
    a = p.parse_args()
    d = json.loads(a.results.read_text())
    result = validate(d)
    if a.selftest:
        mutations = [
            lambda x: x['model']['results'].pop(),
            lambda x: x['model']['results'][1]['output_ids'].__setitem__(0, -1),
            lambda x: x['model']['results'][0].__setitem__('decode_ms', -1),
            lambda x: x['archived_200k_reference']['result']['output_ids'].__setitem__(0, -1),
            lambda x: x['smoke']['results'][2]['requests'][0]['output_ids'].__setitem__(0, -1),
            lambda x: x['api']['disconnect_test'].__setitem__('same_engine_process', False),
        ]
        for mutate in mutations:
            broken = copy.deepcopy(d)
            mutate(broken)
            try:
                validate(broken)
            except (ValueError, KeyError, IndexError):
                continue
            raise RuntimeError('corrupted receipt unexpectedly accepted')
        result['rejected_mutations'] = len(mutations)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
