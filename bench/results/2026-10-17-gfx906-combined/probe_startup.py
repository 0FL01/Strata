#!/usr/bin/env python3
"""Startup-only fresh-container probe. Uses benchmark config; sends only QUIT.
python3 probe_startup.py config.json NEW_OUTPUT_DIR [A|B]
No prompt file, expected_info or required_stderr_fragments are needed.
"""
import fcntl
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess as sp
import sys
import threading
import time
import uuid
from run_pairs import LABEL, cleanup, owned, save, reap_client
from protocol import need


def main():
    cfg=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);arm=sys.argv[3] if len(sys.argv)>3 else 'A'
    need(arm in ('A','B'),'arm must be A or B')
    env=dict(cfg['environment']);env.update(cfg.get('treatment_environment',{}).get(arm,{}))
    need('STRATA_API_KEY' not in env,'API credential is forbidden in native probe environment')
    need(cfg['image'].startswith('sha256:'),'pinned image required')
    owner=uuid.uuid4().hex;name='strata-startup-'+owner[:12]
    cmd=['docker','run','--pull=never','--rm','--init','--name',name,'--label',LABEL+'='+owner,
         '--network','none','-i','--entrypoint','/usr/bin/env']+cfg['docker_options']
    for k,v in sorted(env.items()):cmd+=['-e',k+'='+str(v)]
    cmd += [cfg['image']]
    for k in sorted(set(cfg.get('unset_environment',[]))|{'STRATA_API_KEY'}):
        need(k not in env,'set/unset conflict: '+k);cmd+=['-u',k]
    cmd += [cfg['executables'][arm],'--serve']+cfg['args']
    with open(cfg['lock_path'],'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out.mkdir(parents=True,exist_ok=False)
        receipt=dict(state='starting',owner=owner,container=name,arm=arm,pid=os.getpid(),command=cmd,start_unix=time.time(),generation_requests=0)
        save(out/'receipt.json',receipt)
        p=None;reader=None;lines=queue.Queue()
        def interrupted(sig,frame):raise KeyboardInterrupt('signal '+str(sig))
        previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGTERM,signal.SIGINT)}
        try:
            need(not owned(name,owner),'container already exists')
            with (out/'stderr.log').open('w') as err:
                p=sp.Popen(cmd,stdin=sp.PIPE,stdout=sp.PIPE,stderr=err,text=True,bufsize=1,start_new_session=True)
                receipt['docker_client_pid']=p.pid;save(out/'receipt.json',receipt)
                def read():
                    try:
                        with (out/'stdout.log').open('w') as f:
                            for line in p.stdout:f.write(line);f.flush();lines.put(line.rstrip('\n'))
                    finally:lines.put(None)
                reader=threading.Thread(target=read,daemon=True);reader.start()
                deadline=time.monotonic()+cfg.get('startup_timeout_s',900)
                startup=[]
                while True:
                    need(time.monotonic()<deadline,'startup timeout')
                    try:line=lines.get(timeout=min(1,max(.001,deadline-time.monotonic())))
                    except queue.Empty:continue
                    need(line is not None,'EOF before READY')
                    need(not line.startswith(('ERR ','FATAL ','FAIL ')),line)
                    startup.append(line)
                    if line.startswith('READY '):break
                receipt.update(state='ready',startup=startup,ready_unix=time.time());save(out/'receipt.json',receipt)
                # This request-free engine is waiting on stdin. No GEN is sent.
                os.set_blocking(p.stdin.fileno(),False)
                need(os.write(p.stdin.fileno(),b'QUIT\n')==5,'QUIT write incomplete');p.stdin.close()
                p.wait(timeout=cfg.get('quit_timeout_s',120));reader.join(timeout=30)
                need(not reader.is_alive(),'stdout reader did not close')
                need(p.returncode==0,'native exit failed: '+str(p.returncode))
            all_lines=(out/'stdout.log').read_text().splitlines()
            infos=[x for x in all_lines if x.startswith('INFO ')]
            ready=[x for x in all_lines if x.startswith('READY ')]
            need(len(infos)==len(ready)==1,'expected one INFO and READY')
            need(ready[0]=='READY 262144 stop','exact READY context/protocol mismatch')
            need(all_lines.index(infos[0])<all_lines.index(ready[0]),'INFO must precede READY')
            need(not any(x.strip() for x in all_lines[all_lines.index(ready[0])+1:]),'unexpected output after READY')
            closed_stdout='\n'.join(all_lines)
            closed_stderr=(out/'stderr.log').read_text()
            failure=r'(?im)^\s*(?:ERR|FATAL|FAIL)\b|hipError|illegal memory access|out of memory'
            need(not re.search(failure,closed_stdout),'failure diagnostic in closed stdout')
            need(not re.search(failure,closed_stderr),'failure diagnostic in closed stderr')
            need(not any(x.startswith(('T ','DONE ','RESUME ','REUSED ','PP ')) for x in all_lines),'unexpected generation output')
            fields=infos[0].split()[1:];need(bool(fields) and all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=[^\s]*',x) for x in fields),'malformed INFO')
            info=dict(x.split('=',1) for x in fields);need(len(info)==len(fields),'duplicate INFO')
            receipt.update(state='complete',exit_code=p.returncode,finish_unix=time.time(),info=info,ready=ready[0])
        except BaseException as exc:
            receipt.update(state='failed',error=repr(exc),finish_unix=time.time())
            if p is not None and p.poll() is None:
                try:os.set_blocking(p.stdin.fileno(),False);os.write(p.stdin.fileno(),b'QUIT\n')
                except (OSError,ValueError,AttributeError):pass
                try:p.wait(timeout=cfg.get('interrupt_grace_s',15))
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
                save(out/'receipt.json',receipt)
                for sig,handler in previous.items():signal.signal(sig,handler)
        print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':main()
