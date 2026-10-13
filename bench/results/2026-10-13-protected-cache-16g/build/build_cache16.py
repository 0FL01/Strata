#!/usr/bin/env python3
"""Frozen CPU-only incremental build. Never deploys or starts Strata.

Package contract is documented in PACKAGE_SPEC.md. A closure audit is mandatory:
all donor archive members remain byte-identical except reviewed host members whose
translation units are rebuilt against the complete changed-header layout.
"""
import argparse
import fcntl
import hashlib
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
sys.dont_write_bytecode = True
import prior_recipe as recipe

HERE = Path(__file__).resolve().parent
BASE_BINARY = '74aa76d48a4783991e60b7e25601125dc5dc2bfeeaa351a71b350c122476b662'
BASE_GENERATE = '614034787daa9e5c9a114dc36845cea821f01f44a84b7d1aa2fb6597fd0c671e'
BASE_OBJECT = 'f90e6142d7a5964be5e8bade7244f2893c8d2801fbc557b9bb3471e56190a4a1'
BASE_RECEIPT = '673c0c798e665ea86d0cf925306fadbdeff96249132379c51fd1cd900ff030cb'
BASE_HOST_RECEIPT = 'd106ec0a39d084ebe918ad8455eb78df0d3f2c142e722ec4cd170741a0d92310'
LABEL = 'strata.cache16.cpu.owner'
AR = '/opt/rocm/llvm/bin/llvm-ar'
need, sha, info = recipe.need, recipe.sha, recipe.info


def write(p, value):
    p = Path(p)
    q = p.with_name(p.name + '.tmp')
    q.write_text(json.dumps(value, indent=2) + '\n')
    q.replace(p)


def safe_rel(value):
    p = Path(value)
    need(not p.is_absolute() and '..' not in p.parts and value not in ('', '.'), 'safe relative path: ' + value)
    return p


def seal(expected):
    manifest = HERE / 'SHA256SUMS'
    need(sha(manifest) == expected, 'manifest digest')
    pins = {}
    for line in manifest.read_text().splitlines():
        h, n = line.split('  ', 1)
        safe_rel(n)
        need(n not in pins, 'duplicate package member')
        pins[n] = h
    actual = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p != manifest}
    need(actual == set(pins), 'exact package inventory')
    return recipe.checked(HERE, pins)


def config():
    c = json.loads((HERE / 'package.json').read_text())
    need(c['schema'] == 1, 'package schema')
    need(c['baseline_binary_sha256'] == BASE_BINARY, 'known rollback baseline')
    need(c['generate_compile_argv'] == recipe.command('generate'), 'historical generate optimization flags')
    need(c['link_argv'] == recipe.link_command(Path('/out/build')), 'historical link flags and GPU object')
    need(c['closure']['reviewed'] is True, 'ODR closure reviewed')
    need(c['closure']['complete_dependency_inventory'] is True, 'complete dependency inventory required')
    return c


def donor_pins(c):
    r = json.loads((HERE / 'baseline-build-receipt.json').read_text())
    need(sha(HERE / 'baseline-build-receipt.json') == BASE_RECEIPT, 'known baseline receipt')
    need(sha(HERE / 'baseline-host-receipt.json') == BASE_HOST_RECEIPT, 'known baseline host receipt')
    need(r['passed'] is True and r['binary']['sha256'] == BASE_BINARY, 'passed baseline')
    pins = {n: row['sha256'] for n, row in r['donor_before'].items() if n.endswith('.a') or n == 'hc_bf16_n4.o'}
    pins.update({recipe.OBJECTS['generate']: BASE_OBJECT, 'strata': BASE_BINARY, 'build-receipt.json': BASE_RECEIPT})
    need(c['donor_pins'] == pins, 'baseline donor input map')
    return pins


def dependency_closure(c):
    changed = {n for n, f in c['files'].items() if f.get('candidate') and f['candidate_sha256'] != f.get('baseline_sha256')}
    affected, inventory = [], set()
    rows = c['closure']['linked_tus']
    need(rows, 'nonempty linked TU inventory')
    for row in rows:
        identity = (row.get('archive'), row.get('member'), row['object'])
        need(identity not in inventory, 'duplicate linked TU')
        inventory.add(identity)
        deps = set(row['dependencies']) | {row['source']}
        need(row.get('dependency_evidence'), 'dependency evidence required: ' + row['source'])
        touched = sorted(changed & deps)
        if touched:
            need(row['language'] == 'CXX', 'changed header reaches GPU/C TU; explicit rebuild recipe required: ' + row['source'])
            need(row.get('rebuild') is True, 'affected TU not scheduled: ' + row['source'])
            need(row['source'].endswith(('.cpp', '.cc', '.cxx')), 'host source only')
            need(row['command'][-2:] == ['-c', '/src/' + row['source']], 'fixed host compile source')
            need('-O3' in row['command'] and '-DNDEBUG' in row['command'] and '-std=c++20' in row['command'], 'preserve optimized build flags')
            affected.append(dict(row, changed_dependencies=touched))
        else:
            need(not row.get('rebuild'), 'unexplained rebuilt TU: ' + row['source'])
    need(any(t['source'] == 'src/program/generate.cpp' for t in affected), 'generate closure')
    # Metadata layout changes must cover known by-value owners, even when evidence
    # was accidentally collected from an obsolete or incomplete dependency file.
    if 'include/strata/core/conversation_cache.hpp' in changed:
        sources = {t['source'] for t in affected}
        for name in ('conversation_state.cpp', 'conversation_file.cpp', 'conversation_snapshot.cpp'):
            need(any(Path(s).name == name for s in sources), 'checkpoint ABI owner missing: ' + name)
    return affected


def archive_members(path):
    # Parse regular ar containers directly so duplicate member names in ggml
    # archives are independently hashed, rather than silently concatenated by ar p.
    data = Path(path).read_bytes()
    need(data[:8] == b'!<arch>\n', 'regular, self-contained archive: ' + str(path))
    pos, strings, result = 8, b'', {}
    while pos < len(data):
        need(pos + 60 <= len(data), 'complete archive header')
        head = data[pos:pos + 60]
        need(head[58:] == b'`\n', 'archive header marker')
        size = int(head[48:58].decode('ascii').strip())
        rawname = head[:16].decode('utf-8').strip()
        payload = data[pos + 60:pos + 60 + size]
        need(len(payload) == size, 'complete archive member')
        pos += 60 + size + (size % 2)
        if rawname == '//':
            strings = payload
            continue
        if rawname in ('/', '/SYM64/'):
            continue
        if rawname.startswith('#1/'):
            length = int(rawname[3:])
            name = payload[:length].rstrip(b'\0').decode('utf-8')
            payload = payload[length:]
            if name in ('__.SYMDEF', '__.SYMDEF SORTED'):
                continue
        elif rawname.startswith('/') and rawname[1:].isdigit():
            start = int(rawname[1:])
            need(start < len(strings), 'archive long-name offset')
            end = strings.find(b'/\n', start)
            need(end >= start, 'archive long-name terminator')
            name = strings[start:end].decode('utf-8')
        else:
            name = rawname.removesuffix('/')
        result.setdefault(name, []).append(hashlib.sha256(payload).hexdigest())
    need(pos == len(data), 'archive complete alignment')
    return result


def validate_archive_inventory(c, out):
    actual = {}
    entries = c['closure']['linked_tus']
    for archive in (n for n in c['donor_pins'] if n.endswith('.a')):
        members = archive_members(out / archive)
        actual[archive] = members
        represented = {t['member']: t['baseline_object_sha256'] for t in entries if t.get('archive') == archive}
        need(all(members.get(n) == [h] for n, h in represented.items()), 'reviewed archive member pins: ' + archive)
    return actual


def parse_dependencies(text):
    flat = text.replace('\\\n', ' ')
    need(':' in flat, 'valid make dependency record')
    return {p[5:] for p in shlex.split(flat.split(':', 1)[1]) if p.startswith('/src/')}


def audit_original_dependencies(c):
    evidence = json.loads((HERE / 'dependencies.json').read_text())
    root = Path('/dependency-donor')
    pins = {row['path'].removeprefix('build-906/'): row['sha256'] for row in evidence['dependency_inventory']}
    actual = {str(p.relative_to(root)) for p in root.rglob('*.o.d')}
    need(actual == set(pins), 'complete original dependency inventory unchanged')
    recipe.checked(root, pins)
    changed = {n for n, f in c['files'].items() if f.get('candidate') and f.get('baseline') and f['candidate_sha256'] != f['baseline_sha256']}
    matched = {}
    for n in pins:
        deps = parse_dependencies((root / n).read_text())
        if changed & deps:
            matched[n.removesuffix('.d')] = sorted(changed & deps)
    expected = {t['object'] for t in c['closure']['linked_tus']}
    need(set(matched) == expected, 'exact affected dependency closure')
    return matched


def audit_source_types(c, root, candidate=False):
    root = Path(root)
    evidence = json.loads((HERE / 'source-type-audit.json').read_text())
    expected = {row['path'] for row in evidence}
    found = {}
    needles = ('ConversationCheckpoint', 'SavedConversation', 'conversation_cache.hpp', 'ConversationBuffer', 'conversation_buffer.hpp', 'conversation_snapshot.hpp', 'conversation_file.hpp', 'conversation_copy')
    for folder in ('src', 'include'):
        for p in (root / folder).rglob('*'):
            if not p.is_file() or p.suffix not in ('.cpp', '.cc', '.cxx', '.cu', '.h', '.hpp', '.cuh') or p.name.endswith('_test.cpp'):
                continue
            hits = [line.strip() for line in p.read_text(errors='replace').splitlines() if any(n in line for n in needles)]
            if hits:
                n = str(p.relative_to(root))
                found[n] = dict(sha256=sha(p), hits=hits)
                need(p.suffix not in ('.cu', '.cuh'), 'checkpoint layout touches GPU source: ' + n)
    allowed = expected | {'include/strata/core/conversation_buffer.hpp'} | {row['source'] for row in c['closure']['linked_tus']} | ({n for n, f in c['files'].items() if f.get('candidate')} if candidate else set())
    need(set(found) <= allowed, 'unreviewed checkpoint type/header owner: ' + ', '.join(sorted(set(found) - allowed)))
    need(expected <= set(found), 'historical checkpoint ownership unexpectedly disappeared')
    if not candidate:
        for row in evidence:
            expected_sha = c['closure']['source_pins'].get(row['path'], row['sha256'])
            need(found[row['path']]['sha256'] == expected_sha, 'source audit pin: ' + row['path'])
    return found


def check_source_pins(c, root):
    root = Path(root)
    recipe.checked(root, c['closure']['source_pins'])
    snapshot = {}
    for folder in ('src', 'include'):
        for path in (root / folder).rglob('*'):
            if path.is_file():
                snapshot[str(path.relative_to(root))] = info(path)
    # Image libraries are pinned by immutable image; these external source headers
    # are recorded and checked unchanged around compilation as well.
    for row in c['closure']['linked_tus']:
        for n in row['dependencies']:
            p = root / n
            if p.is_file() and n not in snapshot:
                snapshot[n] = info(p)
    return snapshot


def audit_candidate_dependencies(c, affected, out):
    rows = {}
    seen = set()
    for row in affected:
        p = out / (row['object'] + '.d')
        deps = parse_dependencies(p.read_text())
        rows[row['source']] = dict(dependency_file=info(p), source_dependencies=sorted(deps))
        seen |= deps
    for n, f in c['files'].items():
        if f.get('candidate') and n.endswith(('.hpp', '.h')):
            need(n in seen, 'candidate header not compiled into any production TU: ' + n)
    return rows


def inside(a):
    need(not Path('/dev/kfd').exists() and not Path('/dev/dri').exists(), 'CPU-only: GPU devices absent')
    package_before = seal(a.manifest_sha)
    c = config()
    pins = donor_pins(c)
    affected = dependency_closure(c)
    out = Path('/out/build')
    need(os.path.samefile('/src/build-906', out), 'build output overlay')
    before = recipe.checked('/donor', pins)
    need({p: sha(p) for p in recipe.IMAGE_INPUTS} == recipe.IMAGE_INPUTS, 'image link libraries pinned')
    original_closure = audit_original_dependencies(c)
    source_types_before = audit_source_types(c, '/src')
    source_before = check_source_pins(c, '/src')
    r = dict(passed=False, image=recipe.IMAGE, baseline_binary_sha256=BASE_BINARY,
             manifest_sha256=a.manifest_sha, gpu_execution=False,
             gpu_kernel_translation_units_compiled=0, host_translation_units_compiled=0,
             test_translation_units_compiled=0, steps=[], changed_translation_units=affected,
             dependency_closure=original_closure, source_type_audit_before=source_types_before, source_snapshot_before=source_before)
    def save(): write(out / 'build-receipt.json', r)
    def run(name, argv, timeout=360):
        start = time.monotonic()
        with (out / (name + '.log')).open('xb') as log:
            q = subprocess.run(argv, cwd=out, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        r['steps'].append(dict(name=name, argv=argv, returncode=q.returncode, seconds=time.monotonic()-start))
        save()
        need(q.returncode == 0, name + ' failed')
    save()
    try:
        original_members = validate_archive_inventory(c, out)
        r['baseline_archive_members'] = original_members
        reproduced = {}
        for index, row in enumerate(affected):
            obj = out / safe_rel(row['object'])
            obj.parent.mkdir(parents=True, exist_ok=True)
            run('baseline-' + str(index) + '-' + Path(row['source']).stem, row['command'])
            r['host_translation_units_compiled'] += 1
            reproduced[row['source']] = info(obj)
            need(sha(obj) == row['baseline_object_sha256'], 'baseline object reproduction: ' + row['source'])
        r['baseline_objects_reproduced'] = reproduced
        run('baseline-link', c['link_argv'])
        need(sha(out / 'strata') == BASE_BINARY, 'baseline binary reproduction')
        shutil.copyfile(out / 'strata', out / 'rollback-strata')
        r['baseline_binary_reproduced'] = True
        for n, f in c['files'].items():
            if not f.get('candidate'): continue
            p = Path('/src') / safe_rel(n)
            p.parent.mkdir(parents=True, exist_ok=True)
            need(sha(HERE / f['candidate']) == f['candidate_sha256'], 'candidate pin: ' + n)
            shutil.copyfile(HERE / f['candidate'], p)
        r['candidate_source_files'] = {n: info(Path('/src') / n) for n, f in c['files'].items() if f.get('candidate')}
        for index, test in enumerate(c['cpu_tests']):
            need(test['compile_argv'][0] == '/opt/rocm/llvm/bin/clang++', 'fixed test compiler')
            need('-DNDEBUG' not in test['compile_argv'], 'assert-enabled CPU tests')
            run('test-' + str(index) + '-compile', test['compile_argv'])
            r['test_translation_units_compiled'] += 1
            run('test-' + str(index) + '-run', test['run_argv'])
        need(c['cpu_tests'], 'CPU tests required')
        r['cpu_policy_tests_passed'] = True
        changed_members = {}
        for index, row in enumerate(affected):
            run('candidate-' + str(index) + '-' + Path(row['source']).stem, row['command'])
            r['host_translation_units_compiled'] += 1
            if row.get('archive'):
                obj = out / row['object']
                need(obj.name == row['member'], 'archive member name preserved')
                run('archive-' + str(index), [AR, 'rD', str(out / row['archive']), str(obj)])
                changed_members.setdefault(row['archive'], set()).add(row['member'])
        after_members = {n: archive_members(out / n) for n in original_members}
        for n, old in original_members.items():
            new = after_members[n]
            need(set(new) == set(old), 'archive member set preserved: ' + n)
            for member, h in old.items():
                if member not in changed_members.get(n, set()):
                    need(new[member] == h, 'historical member preserved: ' + n + '(' + member + ')')
        r['candidate_source_type_audit'] = audit_source_types(c, '/src', candidate=True)
        r['candidate_dependencies'] = audit_candidate_dependencies(c, affected, out)
        r['candidate_archive_members'] = after_members
        r['only_reviewed_archive_members_replaced'] = True
        run('candidate-link', c['link_argv'])
        r['symbol_ownership'] = recipe.integration_symbols((out / 'link.map').read_text())
        r['binary'] = info(out / 'strata')
        need(r['binary']['sha256'] != BASE_BINARY, 'candidate must differ from baseline')
        r['link_completed'] = True
    finally:
        r['donor_after'] = recipe.checked('/donor', pins)
        r['donor_unchanged'] = r['donor_after'] == before
        r['gpu_object_unchanged'] = sha(out / 'hc_bf16_n4.o') == pins['hc_bf16_n4.o']
        r['package_unchanged'] = seal(a.manifest_sha) == package_before
        r['candidate_sources_unchanged'] = all(sha(Path('/src') / n) == f['candidate_sha256'] for n, f in c['files'].items() if f.get('candidate'))
        r['rollback_binary_preserved'] = (out / 'rollback-strata').is_file() and sha(out / 'rollback-strata') == BASE_BINARY
        r['untouched_sources_unchanged'] = all(sha(Path('/src') / n) == row['sha256'] for n, row in source_before.items() if not c['files'].get(n, {}).get('candidate'))
        required = ('baseline_binary_reproduced', 'cpu_policy_tests_passed', 'only_reviewed_archive_members_replaced', 'link_completed', 'donor_unchanged', 'gpu_object_unchanged', 'package_unchanged', 'candidate_sources_unchanged', 'rollback_binary_preserved', 'untouched_sources_unchanged')
        r['passed'] = all(r.get(k) is True for k in required) and r['host_translation_units_compiled'] == 2 * len(affected)
        save()
    need(r['passed'], 'CPU build gates')
    print(json.dumps(r['binary']))


def docker_argv(a, name, c):
    out, source, donor = a.out, Path(c['source_root']), Path(c['donor_root'])
    cmd = ['docker','run','--rm','--pull=never','--runtime=runc','--name',name,'--label',LABEL+'='+name,
           '--user','1000:1000','--network','none','--read-only','--cap-drop=ALL','--security-opt','no-new-privileges',
           '--pids-limit','512','--cpus','2','--memory','12g','--memory-swap','12g','--ipc=private',
           '--tmpfs','/tmp:rw,nosuid,nodev,size=2g','-e','HOME=/tmp','-e','TMPDIR=/tmp','-e','PYTHONDONTWRITEBYTECODE=1']
    mounts = [(HERE,'/package',True),(source,'/src',True),(donor,'/donor',True),(out,'/out',False),
              (source/'build-906','/dependency-donor',True),(out/'build','/src/build-906',False),(out/'source/include','/src/include',False),(out/'source/src','/src/src',False)]
    for src,dst,ro in mounts:
        cmd += ['--mount','type=bind,src='+str(src)+',dst='+dst+(',readonly' if ro else '')]
    return cmd + ['-w','/src/build-906','--entrypoint','python3',recipe.IMAGE,'-B','/package/build_cache16.py','--inside','--manifest-sha',a.manifest_sha]


def cleanup(name):
    ids = subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'], text=True, timeout=20).split()
    need(len(ids) <= 1, 'unambiguous owned container')
    if ids:
        owner = subprocess.check_output(['docker','inspect','--format','{{index .Config.Labels "'+LABEL+'"}}',ids[0]], text=True, timeout=20).strip()
        need(owner == name, 'owned container label')
        subprocess.run(['docker','rm','-f',ids[0]], check=True, timeout=45)
    need(not subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'],text=True,timeout=20).strip(), 'owned container cleanup')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--inside',action='store_true'); p.add_argument('--execute',action='store_true')
    p.add_argument('--cpu-window-approved',action='store_true'); p.add_argument('--out',type=Path)
    p.add_argument('--manifest-sha',required=True)
    a = p.parse_args()
    if a.inside: return inside(a)
    package_before = seal(a.manifest_sha)
    c = config(); pins = donor_pins(c); dependency_closure(c)
    need(a.out is not None and a.out.is_absolute(), 'absolute fresh output required')
    need(not a.out.exists() and not a.out.is_symlink(), 'never overwrite output')
    need(a.out.parent.resolve() == a.out.parent, 'canonical output parent')
    name = 'strata-cache16-' + uuid.uuid4().hex[:12]
    cmd = docker_argv(a, name, c)
    if not a.execute:
        print(json.dumps(cmd, indent=2)); return
    need(a.cpu_window_approved, 'root CPU-window admission required')
    need(os.getuid() == os.getgid() == 1000, 'run as 1000:1000')
    donor, source, out = Path(c['donor_root']), Path(c['source_root']), a.out
    with os.fdopen(os.open('/tmp/strata-direct-ff34-ce.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600),'r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',recipe.IMAGE],text=True,timeout=20).strip() == recipe.IMAGE,'installed image pin')
        before = recipe.checked(donor,pins)
        out.mkdir(mode=0o700); (out/'build').mkdir(mode=0o700); (out/'source').mkdir(mode=0o700)
        r = dict(passed=False, command=cmd, donor_before=before, gpu_execution=False)
        try:
            for n,h in pins.items():
                if n in ('strata','build-receipt.json'): continue
                dst = out/'build'/n; dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(donor/n,dst)
                need(sha(dst)==h and not os.path.samefile(dst,donor/n),'independent donor copy: '+n)
            # Full include/src overlays permit new headers without touching checkout.
            for n in ('include','src'):
                shutil.copytree(source/n,out/'source'/n,symlinks=False)
            for n,f in c['files'].items():
                if not f.get('baseline'):
                    need(not (out/'source'/safe_rel(n)).exists(), 'new candidate path unexpectedly exists in baseline: '+n)
                    continue
                src = HERE/f['baseline']; dst=out/'source'/safe_rel(n)
                need(sha(src)==f['baseline_sha256'],'baseline overlay: '+n)
                dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
            need(sha(out/'source/src/program/generate.cpp')==BASE_GENERATE,'frozen active baseline source')
            write(out/'host-receipt.json',r)
            with (out/'container.stdout').open('xb') as so,(out/'container.stderr').open('xb') as se:
                q=subprocess.run(cmd,stdout=so,stderr=se,timeout=1800)
            r['returncode']=q.returncode
            need(q.returncode==0,'CPU build container failed')
            br=json.loads((out/'build/build-receipt.json').read_text())
            need(br['passed'] is True,'inside build receipt')
            r['binary']=info(out/'build/strata'); need(r['binary']==br['binary'],'binary receipt match')
            r['passed']=True
        except BaseException as e:
            r.update(passed=False,error_type=type(e).__name__,error=str(e)); raise
        finally:
            try:
                cleanup(name); r['owned_cleanup_passed']=True
                r['donor_after']=recipe.checked(donor,pins); need(r['donor_after']==before,'immutable donor')
                need(seal(a.manifest_sha)==package_before,'immutable sealed package')
            except BaseException as e:
                r.update(passed=False,final_error=str(e))
            write(out/'host-receipt.json',r)
        need(r['passed'],'host build gates')
        print(json.dumps(r))

if __name__ == '__main__': main()
