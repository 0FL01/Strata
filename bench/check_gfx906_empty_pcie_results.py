#!/usr/bin/env python3
"""Validate preserved receipts, not a replacement for running the GPU/API tests."""
import argparse
import copy
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data):
    model = data['model']['results']
    require([r['tag'] for r in model] == ['A1', 'B1', 'B2', 'A2'], 'ABBA arms')
    qualification = data['qualification']['results']
    require(len(qualification) == 3, 'qualification arms')
    for result in model + qualification:
        n = result['actual_outputs']
        require(result['passed'] and n in (256, 1024), 'failed/incomplete run')
        ids = result['output_ids']
        require(len(ids) == n and all(type(i) is int and 0 <= i < 248320 for i in ids), 'token IDs')
        for metric, count, duration in [('PP', result['prompt_tokens'], 'prompt_ms'), ('TG', n, 'decode_ms')]:
            ms = result[duration]
            require(math.isfinite(ms) and ms > 0, 'invalid duration')
            require(math.isclose(result[metric], count * 1000 / ms, rel_tol=1e-10), 'throughput arithmetic')
        info = result['engine_info']
        require(int(info['expert_slots']) == 19078 and int(info['expert_slots_primary']) == 9900, 'placement')
        require(int(info['context']) == 204800 and int(info['kv_resident']) == 32768, 'capacity')
    require(all(r['prompt_tokens'] == 65536 and r['actual_outputs'] == 1024 for r in model), '64K coverage')
    require(all(r['output_ids'] == model[0]['output_ids'] for r in model), 'ABBA parity')
    a, b = [model[0], model[3]], [model[1], model[2]]
    gain = 100 * (sum(r['TG'] for r in b) / sum(r['TG'] for r in a) - 1)
    pairs = [100 * (y['TG'] / x['TG'] - 1) for x, y in zip(a, b)]
    require(gain >= 1 and min(pairs) > 0, 'performance gate')
    require(math.isclose(gain, data['model']['decision']['TG_gain_pct'], abs_tol=1e-10), 'reported gain')
    q4 = [r for r in qualification if r['prompt_tokens'] == 4096]
    q200 = [r for r in qualification if r['prompt_tokens'] == 200000]
    require(len(q4) == 2 and all(r['actual_outputs'] == 1024 for r in q4), '4K coverage')
    require(q4[0]['output_ids'] == q4[1]['output_ids'], '4K parity')
    require(len(q200) == 1 and q200[0]['actual_outputs'] == 256, '200K coverage')
    require(q200[0]['output_ids'] == data['qualification']['reference200k_output_ids'], '200K archived parity')
    route = data['route']
    require(route['passed'] and route['all3_requests_32_output_ids_equal'] and route['control_no_elision'], 'route receipt')
    require(route['graphs_checked'] == 6 and route['window_sizes'] == [1, 2, 4], 'route coverage')
    pcie = route['actual_pcie_groups_per_layer_window']
    require(len(pcie) == 3 and pcie[0] == pcie[2] == 0 and pcie[1] > 0, 'real positive PCIe work')
    api = data['api']
    require(api['passed'] and api['original_configuration_restored'], 'API/restore receipt')
    require(all(api[k] == 'passed' for k in ['tools', 'vision', 'parking']), 'API coverage')
    require(api['candidate_process_binary_verified'] and api['candidate_flag_whitelist_verified'], 'candidate identity')
    return {'passed': True, 'TG_gain_pct': gain, 'paired_TG_gains_pct': pairs, 'scope': 'receipt validation only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    data = json.loads(args.results.read_text())
    result = validate(data)
    if args.selftest:
        mutations = [
            lambda d: d['model']['results'][1]['output_ids'].__setitem__(0, -1),
            lambda d: d['model']['results'][0].__setitem__('decode_ms', -1),
            lambda d: d['qualification']['reference200k_output_ids'].__setitem__(0, -1),
            lambda d: d['model']['results'].pop(),
            lambda d: d['route']['actual_pcie_groups_per_layer_window'].__setitem__(1, 0),
            lambda d: d['api'].__setitem__('original_configuration_restored', False),
        ]
        for mutate in mutations:
            broken = copy.deepcopy(data)
            mutate(broken)
            try:
                validate(broken)
            except (ValueError, KeyError, IndexError):
                continue
            raise RuntimeError('negative selftest unexpectedly passed')
        result['rejected_mutations'] = len(mutations)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
