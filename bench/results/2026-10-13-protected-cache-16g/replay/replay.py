#!/usr/bin/env python3
"""Bounded native text replay. No SSH/network/service control; explicit argv only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import signal
import statistics
import select
import subprocess
import threading
import time

CAP = 16 * 1024**3
B = 16384
TURN = 248045
VOCAB = 248320

def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()

def save(path, value):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def common_prefix(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))

class Fixture:
    """History grows with THIS arm's outputs, so prompt parity is also checked."""
    def __init__(self, seed, turn=TURN):
        self.turn = turn
        self.header = [turn, 846, 198]
        self.body = [x for x in seed if isinstance(x, int) and 0 <= x < 248000 and x != turn][:4096]
        if len(self.body) < 1024:
            raise ValueError('seed has too few ordinary token IDs')
        self.hist = self.fill([], 117170)
        # A stable root and the explicit old checkpoint at 117170.
        self.hist[10674:10677] = self.header
        self.hist += self.header
        self.ancestor = None
        self.cancel_prompt = None
        self.previous = None
        self.index = 0

    def fill(self, prefix, length):
        if len(prefix) > length:
            raise ValueError('fixture would truncate history')
        n = length - len(prefix)
        return list(prefix) + (self.body * ((n + len(self.body) - 1) // len(self.body)))[:n]

    def branch(self, history, lcp):
        if len(history) <= lcp:
            raise ValueError('branch beyond frontier')
        result = list(history[:lcp]) + [(history[lcp] + 1) % 200000] + self.body[3000:3255] + self.header
        if common_prefix(result, history) != lcp:
            raise AssertionError('exact LCP invariant')
        return result

    def next(self):
        i = self.index
        self.index += 1
        if i == 0:
            name, ids, outputs = 'long117173', self.hist, 32
        elif 1 <= i <= 6:
            ids = self.hist + self.header + self.body[i * 32:i * 32 + 250] + self.header
            name, outputs = f'short{i:02}', 32
        elif i == 7:
            self.ancestor = list(self.hist)
            ids = self.branch(self.hist, 117131)
            name, outputs = 'compact117131', 32
        elif i == 8:
            ids = self.fill(self.hist, 130897) + self.header
            name, outputs = 'decode_cross131072', 512
        elif i == 9:
            ids = self.branch(self.hist, 131100)
            name, outputs = 'decode_rewrite131100', 32
        elif i == 10:
            ids = self.hist + self.header + self.body[512:544] + self.header
            self.cancel_prompt = list(ids)
            name, outputs = 'cancel_decode', 128
        elif i == 11:
            ids = list(self.cancel_prompt)
            name, outputs = 'recover_cancel', 32
        elif i == 12:
            ids = list(self.ancestor) + self.header
            name, outputs = 'restore_ancestor', 32
        else:
            return None
        self.previous = (name, list(ids), outputs)
        return self.previous

    def finish(self, outputs):
        name, ids, _ = self.previous
        if name != 'cancel_decode':
            self.hist = ids + list(outputs)


def parse_done(line, name, ids, tokens, expected_outputs, elapsed):
    fields = line.split()
    if len(fields) < 16:
        raise RuntimeError('unsupported DONE: ' + line)
    row = dict(case=name, input_sha256=digest(ids), input_tokens=len(ids), output_ids=tokens,
               prompt_ms=float(fields[3]), decode_ms=float(fields[4]), finish=fields[5],
               reused=int(fields[8]), read=int(fields[14]), wall_s=elapsed, done=line)
    if int(fields[1]) != len(tokens) or int(fields[2]) != len(ids):
        raise RuntimeError('output/prompt count invariant')
    if not tokens or len(tokens) > expected_outputs or not all(0 <= v < VOCAB for v in tokens):
        raise RuntimeError('output token domain/count')
    if not all(math.isfinite(row[k]) and row[k] >= 0 for k in ('prompt_ms', 'decode_ms', 'wall_s')):
        raise RuntimeError('timing domain')
    if row['reused'] < 0 or row['read'] < 0 or row['read'] + row['reused'] != len(ids):
        raise RuntimeError('incomplete prompt or invalid reuse')
    if name == 'cancel_decode':
        if row['finish'] != 'cancel' or not 8 <= len(tokens) < expected_outputs:
            raise RuntimeError('cancellation did not interrupt decode')
    elif row['finish'] != 'length' or len(tokens) != expected_outputs:
        raise RuntimeError('full native decode required; disable EOS using reviewed argv')
    return row


def protected_evidence(stderr, rows, required):
    if required and re.search(r'protected(?:[- ]cache).*accounting[ _-]breach', stderr, re.IGNORECASE):
        raise RuntimeError('runtime reported protected-cache accounting breach; a prior bounded ledger is insufficient')
    events = []
    for line in stderr.splitlines():
        if '[protected-cache]' not in line:
            continue
        event = dict(re.findall(r'([A-Za-z_]+)=([^\s;]+)', line))
        event['raw'] = line
        events.append(event)
    meters = []
    for event in events:
        if 'total' not in event:
            continue
        if required and not {'req', 'owned', 'total', 'reserved', 'high_water', 'limit', 'coverage'} <= event.keys():
            raise RuntimeError('incomplete optional-cache meter evidence: ' + event['raw'])
        if required and event.get('coverage') != 'complete':
            raise RuntimeError('required protected-cache coverage is not complete: ' + event['raw'])
        # Runtime contract: total ALREADY includes the in-flight reservation.
        total = int(event['total'])
        reserved = int(event.get('reserved', '0'))
        high = int(event.get('high_water', total))
        owned = int(event.get('owned', total - reserved))
        if min(total, reserved, owned, high) < 0 or total != owned + reserved or high < total or max(total, high) > CAP:
            raise RuntimeError('optional-cache memory cap exceeded: ' + event['raw'])
        if 'limit' in event and int(event['limit']) != CAP:
            raise RuntimeError('candidate must use exactly 16 GiB optional-cache limit')
        meters.append(dict(total=total, owned=owned, reserved=reserved, accounted=total, high_water=high,
                           req=int(event.get('req', '0')), event=event.get('event')))
    degraded = [e['raw'] for e in events if e.get('coverage') == 'degraded' or 'degrad' in e.get('event', '')]
    if required:
        if not meters:
            raise RuntimeError('missing all-accounted optional-cache meter evidence')
        if degraded:
            raise RuntimeError('coverage degraded in normal replay: ' + degraded[0])
        # Each request must have an explicit observed accounting point, even without capture.
        missing = sorted(set(range(1, len(rows) + 1)) - {m['req'] for m in meters})
        if missing:
            raise RuntimeError('missing memory meter for requests: ' + str(missing))
        captures = [e for e in events if e.get('event') == 'captured' and e.get('source') == 'decode'
                    and int(e.get('target', '0')) == 131072 and 131072 <= int(e.get('len', '0')) <= 131100]
        if not captures:
            raise RuntimeError('missing safe decode capture crossing target131072')
        rewrite = next(r for r in rows if r['case'] == 'decode_rewrite131100')
        if not 131072 <= rewrite['reused'] <= 131100:
            raise RuntimeError('decode rewrite did not restore the new decode anchor')
        compact = next(r for r in rows if r['case'] == 'compact117131')
        if not 117131 - (B + 4096) < compact['reused'] <= 117131:
            raise RuntimeError('compaction exceeded protected matching-prefix reread bound')
    return dict(protected_event_count=len(events), meter_samples=meters,
                maximum_accounted_bytes=max((m['accounted'] for m in meters), default=None),
                reported_high_water_bytes=max((m['high_water'] for m in meters), default=None),
                memory_limit_bytes=CAP, protected_required=required, degraded_events=degraded)



def capture_metrics(stderr, rows, protected):
    by_req = {row['request_index']: [] for row in rows}
    for line in stderr.splitlines():
        fields = dict(re.findall(r'([A-Za-z_]+)=([^\s;]+)', line))
        if protected:
            if '[protected-cache]' not in line or fields.get('event') != 'captured':
                continue
            elapsed = float(fields['ms']) if 'ms' in fields else None
            if elapsed is None or not math.isfinite(elapsed) or elapsed < 0:
                raise RuntimeError('capture timing unavailable or invalid: ' + line)
            event = dict(length=int(fields['len']), target=int(fields['target']), source=fields['source'],
                         ms=elapsed, reported_bank_bytes=int(fields['bytes']))
        else:
            if '[ckpt-diag]' not in line or fields.get('event') != 'created':
                continue
            event = dict(length=int(fields['len']), target=None, source=fields.get('source'), ms=None,
                         reported_bank_bytes=None)
        req = int(fields.get('req', '0'))
        if req in by_req:
            by_req[req].append(event)
    for row in rows:
        events = by_req[row['request_index']]
        times = [event['ms'] for event in events]
        row['capture_events'] = events
        row['capture_count'] = len(events)
        row['capture_ms'] = sum(times) if all(value is not None for value in times) else None
        row['request_head_capture_count'] = sum(event['source'] == 'request_head' for event in events)
        row['request_head_capture_ms'] = sum(event['ms'] for event in events if event['source'] == 'request_head') if protected else None
        row['prompt_read_tps'] = row['read'] * 1000 / row['prompt_ms'] if row['prompt_ms'] else None
        row['decode_tps'] = len(row['output_ids']) * 1000 / row['decode_ms'] if row['decode_ms'] else None
        row['output_per_wall_second'] = len(row['output_ids']) / row['wall_s'] if row['wall_s'] else None


def aggregate(rows):
    prompt_ms = sum(row['prompt_ms'] for row in rows)
    decode_ms = sum(row['decode_ms'] for row in rows)
    wall_s = sum(row['wall_s'] for row in rows)
    read = sum(row['read'] for row in rows)
    outputs = sum(len(row['output_ids']) for row in rows)
    first_tokens = [row['first_token_ms'] for row in rows]
    captures = [row.get('capture_ms') for row in rows]
    head_times = [row.get('request_head_capture_ms') for row in rows]
    return dict(request_count=len(rows), input_tokens=sum(row['input_tokens'] for row in rows),
                reused_tokens=sum(row['reused'] for row in rows), read_tokens=read, output_tokens=outputs,
                prompt_ms=prompt_ms, decode_ms=decode_ms, total_wall_s=wall_s,
                first_token_ms_mean=statistics.mean(first_tokens) if first_tokens else None,
                first_token_ms_median=statistics.median(first_tokens) if first_tokens else None,
                prompt_read_tps=read * 1000 / prompt_ms if prompt_ms else None,
                decode_tps=outputs * 1000 / decode_ms if decode_ms else None,
                output_per_wall_second=outputs / wall_s if wall_s else None,
                capture_count=sum(row.get('capture_count', 0) for row in rows),
                capture_ms=sum(captures) if all(value is not None for value in captures) else None,
                request_head_capture_count=sum(row.get('request_head_capture_count', 0) for row in rows),
                request_head_capture_ms=sum(head_times) if all(value is not None for value in head_times) else None)


def paired_metrics(baseline, candidate):
    b, c = aggregate(baseline), aggregate(candidate)
    deltas = {}
    for key in ('prompt_ms', 'decode_ms', 'total_wall_s', 'prompt_read_tps', 'decode_tps', 'output_per_wall_second', 'first_token_ms_mean', 'first_token_ms_median'):
        delta = c[key] - b[key] if c[key] is not None and b[key] is not None else None
        deltas[key] = dict(candidate_minus_baseline=delta,
                           percent_change=delta * 100 / b[key] if delta is not None and b[key] else None)
    return dict(baseline=b, candidate=c, changes=deltas)


def stop_owned(p):
    if p is None or p.poll() is not None:
        return
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=10)


def run(a):
    cmd = json.loads(Path(a.command).read_text())
    if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) for x in cmd):
        raise ValueError('command must be a nonempty argv list')
    seed = json.loads(Path(a.seed).read_text())
    fixture = Fixture(seed, a.turn_token)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(tag=a.tag, expected_binary_sha256=a.binary_sha256, command=cmd,
                    seed_sha256=digest(seed), request_count=13, created_unix=time.time(),
                    context=262144, synthetic_text_only=True, quality_evaluation=False,
                    generated_history='Each arm appends its own native output IDs; compare checks exact input hashes.',
                    memory_scope='Optional host conversation-cache state including active, parked, held, transient; not process RSS.')
    save(out / 'manifest.json', manifest)
    q, rows, info = queue.Queue(), [], {}
    p, t = None, None
    arm_deadline = time.monotonic() + a.arm_timeout

    def reader(pipe):
        try:
            with (out / 'stdout.log').open('w') as log:
                for text in pipe:
                    log.write(text)
                    log.flush()
                    q.put(text.rstrip('\n'))
        finally:
            q.put(None)

    def line(deadline):
        left = min(deadline, arm_deadline) - time.monotonic()
        if left <= 0:
            raise TimeoutError('native phase/arm deadline')
        try:
            text = q.get(timeout=left)
        except queue.Empty as error:
            raise TimeoutError('native response timeout') from error
        if text is None:
            raise RuntimeError('native stdout closed unexpectedly')
        if text.startswith(('ERR ', 'FATAL ')):
            raise RuntimeError(text)
        return text

    def send(payload, deadline):
        data = memoryview(payload.encode())
        while data:
            left = min(deadline, arm_deadline) - time.monotonic()
            if left <= 0 or not select.select([], [p.stdin.fileno()], [], left)[1]:
                raise TimeoutError('native stdin write deadline')
            try:
                written = os.write(p.stdin.fileno(), data[:16384])
                data = data[written:]
            except BlockingIOError:
                continue

    with (out / 'stderr.log').open('w') as error_log:
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error_log,
                                 text=True, bufsize=1, start_new_session=True)
            os.set_blocking(p.stdin.fileno(), False)
            t = threading.Thread(target=reader, args=(p.stdout,), daemon=True)
            t.start()
            deadline = time.monotonic() + a.load_timeout
            while True:
                text = line(deadline)
                if text.startswith('INFO '):
                    info.update(dict(x.split('=', 1) for x in text.split()[1:] if '=' in x))
                if text.startswith('READY '):
                    if int(text.split()[1]) != 262144:
                        raise RuntimeError('expected max context262144')
                    break
            if info.get('context') != '262144':
                raise RuntimeError('missing expected production INFO context262144')
            manifest['engine_info'] = info
            save(out / 'manifest.json', manifest)
            while (case := fixture.next()) is not None:
                name, ids, outputs = case
                start, tokens, progress = time.monotonic(), [], []
                stop_sent = False
                first_token_ms = None
                deadline = start + a.request_timeout
                send(f'GEN {outputs} temperature=0 top_p=1 top_k=1 seed=12345 ' + ','.join(map(str, ids)) + '\n', deadline)
                while True:
                    text = line(deadline)
                    if text.startswith('T '):
                        if first_token_ms is None:
                            first_token_ms = (time.monotonic() - start) * 1000
                        tokens.append(int(text.split()[1]))
                        if name == 'cancel_decode' and len(tokens) >= 8 and not stop_sent:
                            send('STOP\n', deadline)
                            stop_sent = True
                    elif text.startswith('PP '):
                        progress.append(text)
                    elif text.startswith('DONE '):
                        break
                row = parse_done(text, name, ids, tokens, outputs, time.monotonic() - start)
                if first_token_ms is None or not math.isfinite(first_token_ms) or not 0 <= first_token_ms <= row['wall_s'] * 1000:
                    raise RuntimeError('first-token timing domain')
                row.update(request_index=len(rows) + 1, pp=progress, stop_sent=stop_sent, first_token_ms=first_token_ms)
                rows.append(row)
                fixture.finish(tokens)
                save(out / 'results.json', rows)
                print(json.dumps({k: v for k, v in row.items() if k not in ('output_ids', 'pp', 'done')}), flush=True)
            send('QUIT\n', time.monotonic() + 10)
            p.stdin.close()
            p.wait(timeout=min(60, max(1, arm_deadline - time.monotonic())))
            t.join(timeout=5)
            if p.returncode or t.is_alive():
                raise RuntimeError('unclean native exit')
            error_log.flush()
            stderr = (out / 'stderr.log').read_text()
            evidence = protected_evidence(stderr, rows, a.require_protected)
            capture_metrics(stderr, rows, a.require_protected)
            save(out / 'results.json', rows)
            summary = dict(protocol_passed=True, request_count=len(rows), protected_gates_passed=a.require_protected,
                           memory_evidence=evidence, clean_native_exit=True,
                           aggregate=aggregate(rows), ordinary_short_turns=aggregate([r for r in rows if r['case'].startswith('short')]),
                           note='Operator verifies binary hash, devices, API exclusion and owned container cleanup. No image/semantic quality or universal GPU-state claim.')
            save(out / 'summary.json', summary)
            return summary
        except BaseException as error:
            save(out / 'failure.json', dict(type=type(error).__name__, error=str(error), completed_requests=len(rows)))
            raise
        finally:
            stop_owned(p)
            if t:
                t.join(timeout=5)


def compare(a):
    baseline = json.loads(Path(a.baseline, 'results.json').read_text())
    candidate = json.loads(Path(a.candidate, 'results.json').read_text())
    if len(baseline) != 13 or len(candidate) != 13:
        raise ValueError('incomplete arms')
    result = []
    for x, y in zip(baseline, candidate):
        if x['case'] != y['case']:
            raise ValueError('case-order mismatch')
        same_input = x['input_sha256'] == y['input_sha256']
        cancel = x['case'] == 'cancel_decode'
        shared = min(len(x['output_ids']), len(y['output_ids']))
        same_output = (x['output_ids'][:shared] == y['output_ids'][:shared] and shared >= 8) if cancel else x['output_ids'] == y['output_ids']
        result.append(dict(case=x['case'], identical_input=same_input, output_ids_equal=same_output,
                           comparison='common cancellation prefix' if cancel else 'full exact output IDs',
                           baseline_output_tokens=len(x['output_ids']), candidate_output_tokens=len(y['output_ids']),
                           baseline_reused=x['reused'], candidate_reused=y['reused'],
                           baseline_read=x['read'], candidate_read=y['read'], read_reduction=x['read'] - y['read'],
                           baseline_prompt_ms=x['prompt_ms'], candidate_prompt_ms=y['prompt_ms'],
                           baseline_decode_ms=x['decode_ms'], candidate_decode_ms=y['decode_ms'],
                           baseline_wall_s=x['wall_s'], candidate_wall_s=y['wall_s'],
                           baseline_first_token_ms=x['first_token_ms'], candidate_first_token_ms=y['first_token_ms'],
                           baseline_prompt_read_tps=x.get('prompt_read_tps'), candidate_prompt_read_tps=y.get('prompt_read_tps'),
                           baseline_decode_tps=x.get('decode_tps'), candidate_decode_tps=y.get('decode_tps'),
                           baseline_capture_count=x.get('capture_count'), candidate_capture_count=y.get('capture_count'),
                           baseline_capture_ms=x.get('capture_ms'), candidate_capture_ms=y.get('capture_ms'),
                           baseline_capture_events=x.get('capture_events', []), candidate_capture_events=y.get('capture_events', []),
                           candidate_request_head_capture_ms=y.get('request_head_capture_ms')))
    compact = next(r for r in result if r['case'] == 'compact117131')
    decode = next(r for r in result if r['case'] == 'decode_rewrite131100')
    value = dict(rows=result,
                 aggregate=paired_metrics(baseline, candidate),
                 noncancel_aggregate=paired_metrics([r for r in baseline if r['case'] != 'cancel_decode'], [r for r in candidate if r['case'] != 'cancel_decode']),
                 ordinary_short_turns=paired_metrics([r for r in baseline if r['case'].startswith('short')], [r for r in candidate if r['case'].startswith('short')]),
                 decode_anchor_reuse=131072 <= decode['candidate_reused'] <= 131100, all_inputs_identical=all(r['identical_input'] for r in result),
                 all_comparable_output_ids_equal=all(r['identical_input'] and r['output_ids_equal'] for r in result),
                 compaction_read_reduction=compact['read_reduction'], compaction_gain=compact['read_reduction'] > 0,
                 note='One paired run: timing differences are diagnostic, not statistical proof. Short-turn overhead includes request-head copies. Baseline capture timing is uninstrumented (null). Divergent dynamic inputs invalidate later parity comparisons. No semantic quality, images, or universal GPU-state proof.')
    print(json.dumps(value, indent=2))
    return value


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest='mode', required=True)
    r = modes.add_parser('run')
    for field in ('command', 'seed', 'out', 'tag', 'binary-sha256'):
        r.add_argument('--' + field, required=True)
    r.add_argument('--turn-token', type=int, default=TURN)
    r.add_argument('--load-timeout', type=float, default=300)
    r.add_argument('--request-timeout', type=float, default=900)
    r.add_argument('--arm-timeout', type=float, default=2400)
    r.add_argument('--require-protected', action='store_true')
    c = modes.add_parser('compare')
    c.add_argument('--baseline', required=True)
    c.add_argument('--candidate', required=True)
    args = parser.parse_args()
    if args.mode == 'run':
        run(args)
    else:
        result = compare(args)
        if not result['all_comparable_output_ids_equal'] or not result['compaction_gain'] or not result['decode_anchor_reuse']:
            raise SystemExit(1)

if __name__ == '__main__':
    def interrupted(signum, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise InterruptedError('received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    main()
