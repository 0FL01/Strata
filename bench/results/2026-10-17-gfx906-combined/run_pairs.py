#!/usr/bin/env python3
"""Fresh-container benchmark runner. See CONFIG.example.json and README.md.
Run via root's SSH under nohup. Never starts a second run in an existing output
folder. A lock spans all runs sharing lock_path. No auto-retry of failed arms.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import select
import signal
import subprocess as sp
import threading
import time
import uuid
from protocol import ORDER, need, parse, summary

PROMPT_SHA='63ce3d4042027a00b2193feab143f1d9443b5c31a863a962ec9543ccb54d9695'
LABEL='strata.combined-benchmark.owner'

def save(path, obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2)+'\n')
    tmp.replace(path)

def command(argv, timeout=30):
    return sp.run(argv,stdin=sp.DEVNULL,stdout=sp.PIPE,stderr=sp.PIPE,text=True,timeout=timeout)

def owned(name, owner):
    r=command(['docker','inspect',name])
    if r.returncode:
        # Missing container is acceptable, daemon/transport failures are not.
        missing=re.fullmatch(r'(?i:(?:error:|error response from daemon:)\s*no such (?:object|container):)\s*(\S+)',r.stderr.strip())
        need(missing is not None and missing.group(1)==name and r.stdout.strip() in ('','[]'),
             'cannot inspect container: '+r.stderr)
        return False
    info=json.loads(r.stdout)[0]
    need(info['Config'].get('Labels',{}).get(LABEL)==owner,'container ownership mismatch')
    return True

def cleanup(name, owner):
    if owned(name,owner):
        r=command(['docker','stop','--time','20',name],45)
        need(r.returncode==0,'owned container stop failed: '+r.stderr)
    # --rm should have removed it. Do not blindly kill/rm unrelated containers.
    need(not owned(name,owner),'owned container remains after stop')


def reap_client(process, reader, timeout=15):
    """Reap only the local Popen process group created with start_new_session.
    This runs even if Docker ownership inspection/stop failed. It never signals
    a container through Docker and does not assert that a container was removed.
    """
    if process is not None:
        if process.poll() is None:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:process.wait(timeout=timeout)
            except sp.TimeoutExpired:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait(timeout=timeout)
        else:process.wait(timeout=timeout)
    if reader is not None:
        reader.join(timeout=timeout)
        need(not reader.is_alive(),'local stdout reader did not exit after client reap')
    if process is not None:
        for stream in (process.stdin,process.stdout):
            if stream is not None and not stream.closed:
                try:stream.close()
                except BrokenPipeError:pass


def measure(cfg, arm, tag, out, owner, ids, receipt, *, prompt_count=65536, output_count=1024, ignore_info_fields=('vram_free_mib','engine')):
    need(len(ids)==prompt_count, 'explicit prompt length mismatch')
    name='strata-combined-'+owner[:12]+'-'+tag.lower()
    env=dict(cfg['environment'])
    env.update(cfg.get('treatment_environment',{}).get(arm,{}))
    need('STRATA_API_KEY' not in env,'API credential forbidden in native benchmark')
    cmd=['docker','run','--pull=never','--rm','--init','--name',name,'--label',LABEL+'='+owner,
         '--network','none','-i','--entrypoint','/usr/bin/env']+cfg['docker_options']
    for key,value in sorted(env.items()):cmd+=['-e',key+'='+str(value)]
    cmd += [cfg['image']]
    for key in sorted(set(cfg.get('unset_environment',[]))|{'STRATA_API_KEY'}):
        need(key not in env,'environment set/unset conflict: '+key)
        cmd += ['-u',key]
    cmd += [cfg['executables'][arm],'--serve']+cfg['args']
    receipt.update(state='starting',container=name,command=cmd,start_unix=time.time())
    save(out/(tag+'.receipt.json'),receipt)
    need(not owned(name,owner),'refusing duplicate container')
    q=queue.Queue()
    p=None
    reader=None
    log=out/(tag+'.stdout')
    def interrupt(signum,frame):
        raise KeyboardInterrupt('signal '+str(signum))
    previous={sig:signal.signal(sig,interrupt) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        with (out/(tag+'.stderr')).open('w') as err:
            p=sp.Popen(cmd,stdin=sp.PIPE,stdout=sp.PIPE,stderr=err,text=True,bufsize=1,start_new_session=True)
            receipt['docker_client_pid']=p.pid
            save(out/(tag+'.receipt.json'),receipt)
            def read():
                try:
                    with log.open('w') as f:
                        for line in p.stdout:
                            f.write(line);f.flush();q.put(line.rstrip('\n'))
                finally:q.put(None)
            reader=threading.Thread(target=read,daemon=True);reader.start()
            def get(deadline):
                while time.monotonic()<deadline:
                    try:line=q.get(timeout=min(1,max(.001,deadline-time.monotonic())))
                    except queue.Empty:continue
                    need(line is not None,'native stdout closed before DONE')
                    need(not line.startswith(('ERR ','FATAL ','FAIL ')),line)
                    return line
                raise TimeoutError('native stream deadline')
            deadline=time.monotonic()+cfg.get('startup_timeout_s',900)
            startup=[]
            while True:
                line=get(deadline);startup.append(line)
                if line.startswith('READY '):break
            infos=[x for x in startup if x.startswith('INFO ')]
            need(len(infos)==1,'expected startup INFO')
            actual=dict(x.split('=',1) for x in infos[0].split()[1:])
            for key,value in cfg['expected_info'].items():
                need(actual.get(key)==str(value),'startup mismatch '+key)
            need(startup[-1]=='READY 262144 stop','READY mismatch')
            for fragment in cfg['required_stderr_fragments']:
                need(fragment in (out/(tag+'.stderr')).read_text(),'missing startup device/split: '+fragment)
            receipt.update(state='generating',startup=startup,gen_start_unix=time.time())
            save(out/(tag+'.receipt.json'),receipt)
            payload=memoryview((f'GEN {output_count} temperature=0 top_p=1 top_k=1 seed=12345 '+','.join(map(str,ids))+'\n').encode())
            os.set_blocking(p.stdin.fileno(),False)
            deadline=time.monotonic()+cfg.get('generation_timeout_s',7200)
            while payload:
                need(time.monotonic()<deadline,'GEN write timeout')
                if select.select([], [p.stdin], [], 1)[1]:
                    try:n=os.write(p.stdin.fileno(),payload[:16384]);need(n>0,'GEN write stalled');payload=payload[n:]
                    except BlockingIOError:pass
            while True:
                line=get(deadline)
                if line.startswith('DONE '):break
            need(os.write(p.stdin.fileno(),b'QUIT\n')==5,'QUIT write incomplete')
            p.stdin.close()
            p.wait(timeout=cfg.get('quit_timeout_s',120))
            reader.join(timeout=30)
            need(not reader.is_alive(),'stdout reader did not finish')
            need(p.returncode==0,'native exit failed: '+str(p.returncode))
        row=parse(log.read_text(),prompt_count=prompt_count,output_count=output_count,ignore_info_fields=ignore_info_fields)
        stderr=(out/(tag+'.stderr')).read_text()
        for pattern in cfg.get('required_stderr_fragments',[]):
            need(pattern in stderr,'missing expected device/split startup: '+pattern)
        import re
        need(not re.search(r'(?im)^\s*(?:ERR|FATAL|FAIL)\b|hipError|illegal memory access|out of memory',stderr),'failure diagnostic in stderr')
        row.update(pair=receipt['pair'],arm=arm)
        receipt.update(state='complete',exit_code=p.returncode,finish_unix=time.time(),result=row)
        save(out/(tag+'.receipt.json'),receipt)
        return row
    except BaseException as exc:
        receipt.update(state='failed',error=repr(exc),finish_unix=time.time())
        save(out/(tag+'.receipt.json'),receipt)
        # STOP reaches the request through its stdin reader; QUIT ends the loop
        # after cancellation. Give that cooperative path a bounded opportunity.
        if p is not None and p.poll() is None:
            try:os.write(p.stdin.fileno(),b'STOP\nQUIT\n')
            except (OSError,ValueError,AttributeError):pass
            try:p.wait(timeout=30)
            except sp.TimeoutExpired:pass
        raise
    finally:
        for sig in previous:signal.signal(sig,signal.SIG_IGN)
        cleanup_error=None
        try:
            try:cleanup(name,owner)
            except BaseException as exc:
                cleanup_error=exc
                receipt.update(state='cleanup_failed',cleanup_error=repr(exc))
            finally:
                try:
                    reap_client(p,reader,cfg.get('client_reap_timeout_s',15))
                    receipt.update(client_reaped=True,reader_exited=True,
                                   client_exit_code=None if p is None else p.returncode)
                except BaseException as exc:
                    receipt.update(state='cleanup_failed',reap_error=repr(exc))
                    if cleanup_error is None:cleanup_error=exc
            if cleanup_error is not None:raise cleanup_error
        finally:
            save(out/(tag+'.receipt.json'),receipt)
            for sig,handler in previous.items():signal.signal(sig,handler)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('config');ap.add_argument('output');a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text())
    need(cfg.get('protocol_source_commit')=='477ac13cbe8e582c20484871ce459d20d82df09d','source protocol pin missing')
    need('STRATA_API_KEY' not in cfg['environment'] and all('STRATA_API_KEY' not in e for e in cfg.get('treatment_environment',{}).values()),'API credential forbidden in benchmark config')
    need(cfg.get('expected_info') and cfg.get('required_stderr_fragments'),'fresh startup layout must be supplied')
    need(cfg['image'].startswith('sha256:'),'use pinned image ID')
    need('--lookup-chain' not in cfg['args'],'lookup-chain is outside this protocol')
    prompt=Path(cfg['prompt'])
    need(hashlib.sha256(prompt.read_bytes()).hexdigest()==PROMPT_SHA,'frozen prompt SHA mismatch')
    ids=json.loads(prompt.read_text())
    need(len(ids)==65536 and all(type(x) is int and x>=0 for x in ids),'prompt token fixture invalid')
    owner=uuid.uuid4().hex
    with open(cfg['lock_path'],'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
        save(out/'config.json',cfg)
        state=dict(owner=owner,pid=os.getpid(),state='running',order=ORDER,prompt_sha256=PROMPT_SHA,rows=[])
        save(out/'status.json',state)
        try:
            for i,order in enumerate(ORDER,1):
                for arm in order:
                    tag=f'{i:02d}{arm}'
                    row=measure(cfg,arm,tag,out,owner,ids,dict(pair=i,arm=arm),prompt_count=65536,output_count=1024)
                    if state['rows']:
                        ref=state['rows'][0]
                        if not all(row[k]==ref[k] for k in ('output_ids','token_sha256','counters','info')):
                            path=out/(tag+'.receipt.json');receipt=json.loads(path.read_text())
                            receipt.update(state='rejected',error='strict output/work/layout parity mismatch')
                            save(path,receipt)
                            raise ValueError('strict output/work/layout parity failed in '+tag)
                    state['rows'].append(row)
                    save(out/'status.json',state)
                    print(json.dumps(dict(tag=tag,prompt_ms=row['prompt_ms'],decode_ms=row['decode_ms'])),flush=True)
            save(out/'summary.json',summary(state['rows']))
            state['state']='complete'
        except BaseException as exc:
            state.update(state='failed',error=repr(exc))
            raise
        finally:save(out/'status.json',state)

if __name__=='__main__':main()
