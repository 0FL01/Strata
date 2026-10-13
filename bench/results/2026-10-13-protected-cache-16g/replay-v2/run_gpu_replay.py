#!/usr/bin/env python3
"""Root/operator launcher. Explicit admission, pinned binaries, exclusive bounded GPU arms.
Never deploys, changes a production config, uses SSH, or stops a foreign job.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = Path('/srv/strata')
LABEL = 'strata.cache16g.replay.owner'
BASELINE_SHA256 = '74aa76d48a4783991e60b7e25601125dc5dc2bfeeaa351a71b350c122476b662'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as file:
        for data in iter(lambda: file.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def save(path, value):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def sh(argv, timeout=30):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()

def option(argv, key, default=None):
    indices = [i for i, value in enumerate(argv) if value == key]
    if len(indices) > 1:
        raise RuntimeError('duplicate native option: ' + key)
    return argv[indices[0] + 1] if indices else default

def telemetry():
    rows = []
    for pci in ('0000:05:00.0', '0000:08:00.0'):
        path = Path('/sys/bus/pci/devices') / pci
        temps = {p.name: int(p.read_text()) / 1000 for p in path.glob('hwmon/hwmon*/temp*_input')}
        if 'temp1_input' not in temps:
            raise RuntimeError('GPU temperature evidence unavailable: ' + pci)
        rows.append(dict(pci=pci, busy=int((path / 'gpu_busy_percent').read_text()), temps=temps))
    return rows

def check_temp(rows):
    for row in rows:
        for sensor, value in row['temps'].items():
            if value >= (80 if sensor == 'temp1_input' else 90):
                raise RuntimeError('GPU thermal stop: ' + str(row))

def gpu_exclusion(timeout=30):
    deadline = time.monotonic() + timeout
    path = Path('/sys/class/kfd/kfd/proc')
    if not path.is_dir():
        raise RuntimeError('GPU process evidence unavailable')
    while True:
        if not sh(['docker', 'ps', '-q']) and not list(path.glob('[0-9]*')):
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('GPU exclusion blocked: a container or GPU process remains')
        time.sleep(1)

def stop_runner(proc):
    if proc is None or proc.poll() is not None:
        return
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=15)

def cleanup(name, owner):
    found = sh(['docker', 'ps', '-aq', '--filter', 'name=^/' + name + '$']).split()
    if len(found) > 1:
        raise RuntimeError('ambiguous owned container name')
    if found:
        actual = sh(['docker', 'inspect', '--format', '{{index .Config.Labels "' + LABEL + '"}}', found[0]])
        if actual != owner:
            raise RuntimeError('refusing cleanup of foreign container: ' + name)
        subprocess.run(['docker', 'rm', '-f', found[0]], check=True, timeout=30, stdout=subprocess.DEVNULL)
    if sh(['docker', 'ps', '-aq', '--filter', 'name=^/' + name + '$']):
        raise RuntimeError('owned container survived cleanup')

def command(exe, args, env, name, owner, protected):
    native = list(args)
    # Current live launcher enables spread even if the JSON args omit it.
    if '--prompt-cache-spread' not in native:
        native += ['--prompt-cache-spread']
    if '--eos-ids' in native:
        i = native.index('--eos-ids')
        del native[i:i + 2]
    cmd = ['docker', 'run', '--rm', '--pull=never', '--runtime=runc', '--read-only',
           '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m', '--log-driver', 'none', '-i',
           '--name', name, '--label', LABEL + '=' + owner, '--user', '1000:1000',
           '--network', 'none', '--device', '/dev/kfd', '--device', '/dev/dri', '--group-add', '990',
           '--ipc', 'host', '--ulimit', 'memlock=-1:-1', '--entrypoint', '/usr/bin/env']
    for key, value in sorted(env['ENV'].items()):
        cmd += ['-e', key + '=' + value]
    for src, dst in ((str(ROOT), '/src'), ('/srv/models-nvme', '/models'), ('/srv/models', '/sata')):
        cmd += ['-v', src + ':' + dst + ':ro']
    cmd += [env['IMAGE']]
    for key in env['ABSENT']:
        cmd += ['-u', key]
    cmd += ['/src/' + str(Path(exe).relative_to(ROOT)), '--serve'] + native + ['--eos-ids', '2147483647']
    if protected:
        cmd += ['--prompt-cache-protected']
    return cmd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu-window-approved', action='store_true', required=True)
    for flag in ('production-config', 'baseline-binary', 'baseline-sha256', 'candidate-binary', 'candidate-sha256', 'build-receipt', 'out'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--api-name', default='strata-api')
    parser.add_argument('--arm-timeout', type=int, default=2400)
    args = parser.parse_args()
    if not args.gpu_window_approved:
        raise RuntimeError('explicit operator GPU-window admission required')
    if args.baseline_sha256 != BASELINE_SHA256:
        raise RuntimeError('only the current live spread6 baseline is admitted')
    out = Path(args.out)
    if out.exists():
        raise RuntimeError('fresh output directory required')
    if not 120 <= args.arm_timeout <= 7200:
        raise RuntimeError('arm timeout outside approved bounded range')
    env = json.loads((HERE / 'production-environment.json').read_text())
    config_path = Path(args.production_config)
    config_hash = sha(config_path)
    native = json.loads(config_path.read_text())['args']
    if not isinstance(native, list) or not all(isinstance(v, str) for v in native):
        raise RuntimeError('production config args must be strings')
    expected = {'--max-context': '262144', '--prompt-cache': '6', '--prompt-cache-every': '16384',
                '--conversation-cache-mib': '12288', '--conversation-cache-slots': '4', '--layer-split': '27',
                '--spec': '6', '--prefill': '4096'}
    for key, value in expected.items():
        if option(native, key) != value:
            raise RuntimeError('production geometry mismatch: ' + key)
    for key, value in {'--turn-token': '248045', '--batch': '0', '--pipeline-windows': '0',
                       '--conversation-cache-min-free-mib': '8192', '--slots': '0'}.items():
        if option(native, key, value) != value:
            raise RuntimeError('unsupported production setting: ' + key)
    if '--vision' not in native or '--prompt-cache-protected' in native:
        raise RuntimeError('expected vision-capable, currently unprotected baseline config')
    bins = {'baseline': (Path(args.baseline_binary).resolve(), args.baseline_sha256),
            'candidate': (Path(args.candidate_binary).resolve(), args.candidate_sha256)}
    for tag, (path, expected_hash) in bins.items():
        path.relative_to(ROOT)
        if sha(path) != expected_hash:
            raise RuntimeError('binary hash mismatch: ' + tag)
    receipt = json.loads(Path(args.build_receipt).read_text())
    if receipt.get('passed') is not True or receipt.get('binary', {}).get('sha256') != args.candidate_sha256:
        raise RuntimeError('candidate build acceptance receipt failed or hash does not match')
    if sh(['docker', 'image', 'inspect', '--format', '{{.Id}}', env['IMAGE']]) != env['IMAGE']:
        raise RuntimeError('pinned image mismatch')
    owner = uuid.uuid4().hex
    names = {tag: 'strata-cache16g-' + tag + '-' + owner[:12] for tag in bins}
    for name in names.values():
        if sh(['docker', 'ps', '-aq', '--filter', 'name=^/' + name + '$']):
            raise RuntimeError('owned name unexpectedly exists')
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    status = dict(passed=False, started_unix=time.time(), owner=owner, arms={},
                  production_config_sha256=config_hash, build_receipt_sha256=sha(args.build_receipt),
                  binary_sha256={tag: value[1] for tag, value in bins.items()},
                  gpu_execution=True, synthetic_text_only=True)
    save(out / 'status.json', status)
    proc, stop_attempted, was_running = None, False, False
    lock_fd = os.open('/tmp/strata-direct-ff34-ce.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(lock_fd, 'a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        running = sh(['docker', 'inspect', '--format', '{{.State.Running}}', args.api_name])
        if running not in ('true', 'false'):
            raise RuntimeError('API state unavailable')
        was_running = running == 'true'
        status['api_was_running'] = was_running
        if was_running:
            stop_attempted = True
            subprocess.run(['docker', 'stop', '--time', '30', args.api_name], check=True, timeout=90, stdout=subprocess.DEVNULL)
        gpu_exclusion()
        for tag, (exe, expected_hash) in bins.items():
            deadline = time.monotonic() + 240
            while True:
                sample = telemetry()
                check_temp(sample)
                if all(row['busy'] <= 1 and row['temps']['temp1_input'] <= 55 for row in sample):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError('GPU idle/cooldown deadline')
                time.sleep(2)
            gpu_exclusion()
            if sha(exe) != expected_hash or sha(config_path) != config_hash:
                raise RuntimeError('binary/config changed before launch')
            save(out / (tag + '-gpu-before.json'), sample)
            cmd = command(exe, native, env, names[tag], owner, tag == 'candidate')
            save(out / (tag + '-command.json'), cmd)
            runner = [sys.executable, '-B', str(HERE / 'replay.py'), 'run', '--command', str(out / (tag + '-command.json')),
                      '--seed', str(HERE / 'prompt-65536.ids.json'), '--out', str(out / tag), '--tag', tag,
                      '--binary-sha256', expected_hash, '--arm-timeout', str(args.arm_timeout)]
            if tag == 'candidate':
                runner += ['--require-protected']
            else:
                runner += ['--require-root-reproduction']
            status['current_arm'] = tag
            save(out / 'status.json', status)
            samples, proc = [], None
            try:
                with (out / (tag + '-runner.log')).open('x') as log:
                    proc = subprocess.Popen(runner, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    deadline = time.monotonic() + args.arm_timeout + 30
                    while proc.poll() is None:
                        samples.append(dict(unix=time.time(), gpus=telemetry()))
                        check_temp(samples[-1]['gpus'])
                        if time.monotonic() >= deadline:
                            raise RuntimeError('outer arm deadline')
                        time.sleep(3)
                if proc.returncode:
                    raise RuntimeError('replay failed: ' + tag + ' rc=' + str(proc.returncode))
            finally:
                try:
                    stop_runner(proc)
                finally:
                    try:
                        cleanup(names[tag], owner)
                    finally:
                        save(out / (tag + '-gpu-samples.json'), samples)
            gpu_exclusion()
            save(out / (tag + '-gpu-after.json'), telemetry())
            summary = json.loads((out / tag / 'summary.json').read_text())
            if not summary.get('protocol_passed') or (tag == 'candidate' and not summary.get('protected_gates_passed')):
                raise RuntimeError('replay summary gate failed')
            if tag == 'baseline' and not summary.get('root_reproduction_passed'):
                raise RuntimeError('baseline root-collapse reproduction gate failed; candidate not launched')
            status['arms'][tag] = summary
            save(out / 'status.json', status)
        result = subprocess.run([sys.executable, '-B', str(HERE / 'replay.py'), 'compare', '--baseline', str(out / 'baseline'),
                                 '--candidate', str(out / 'candidate')], capture_output=True, text=True, timeout=30)
        if result.stdout.strip():
            comparison = json.loads(result.stdout)
            save(out / 'comparison.json', comparison)
            status.update(exact_output_ids_equal=comparison['all_comparable_output_ids_equal'],
                          all_inputs_identical=comparison['all_inputs_identical'],
                          compaction_read_reduction=comparison['compaction_read_reduction'],
                          decode_anchor_reuse=comparison['decode_anchor_reuse'],
                          baseline_root_reproduction=comparison['baseline_root_reproduction'],
                          aggregate=comparison['aggregate'], ordinary_short_turns=comparison['ordinary_short_turns'])
        if result.returncode:
            raise RuntimeError('paired parity or compaction-gain acceptance failed')
        status['passed'] = True
    except BaseException as error:
        status.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        status.update(finished_unix=time.time(), api_stop_attempted=stop_attempted)
        try:
            stop_runner(proc)
            for name in names.values():
                cleanup(name, owner)
            gpu_exclusion()
            status['owned_cleanup_passed'] = True
            if stop_attempted:
                subprocess.run(['docker', 'start', args.api_name], check=True, timeout=45, stdout=subprocess.DEVNULL)
                status['api_start_requested'] = True
            status['production_config_unchanged'] = sha(config_path) == config_hash
            status['binary_inputs_unchanged'] = all(sha(path) == expected_hash for path, expected_hash in bins.values())
            if not status['production_config_unchanged'] or not status['binary_inputs_unchanged']:
                status['passed'] = False
        except BaseException as error:
            status.update(passed=False, recovery_error_type=type(error).__name__, recovery_error=str(error))
            raise
        finally:
            save(out / 'status.json', status)
            lock.close()

if __name__ == '__main__':
    def interrupted(signum, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise InterruptedError('received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    main()
