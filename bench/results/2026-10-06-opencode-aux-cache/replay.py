import os,json,time,urllib.request
from pathlib import Path
import argparse
ap=argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:8080")
ap.add_argument("--output", type=Path, required=True)
ap.add_argument("--execute", action="store_true")
ap.add_argument("--records", type=int, default=350)
a=ap.parse_args()
if not a.execute: ap.error("--execute is required: this runs inference and replaces the active prefix cache")
base=a.url.rstrip("/")
headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ['STRATA_API_KEY'],'x-opencode-session-id':'synthetic-cache-recon','x-session-affinity':'synthetic-cache-recon','X-Session-Id':'synthetic-cache-recon'}
context=chr(10).join('Record '+str(i)+': alpha beta gamma delta; value='+str(i*7)+'.' for i in range(a.records))
main={'model':'current','messages':[{'role':'system','content':'You are a coding assistant. Use the supplied synthetic records as context. Answer the final arithmetic question with only the integer.'},{'role':'user','content':context+chr(10)+'What is 17 + 25?'}],'temperature':0,'max_tokens':32,'chat_template_kwargs':{'enable_thinking':False}}
title={'model':'current','messages':[{'role':'system','content':'You are a title generator. You output ONLY a thread title. Nothing else.'},{'role':'user','content':'Generate a title for this conversation: Synthetic record processing and arithmetic.'}],'tools':[],'temperature':0,'max_tokens':32,'chat_template_kwargs':{'enable_thinking':False}}
rows=[]
for tag,body in [('main_cold',main),('main_warm',main),('aux_title',title),('main_after_title',main),('main_rewarm',main)]:
 started=time.monotonic();req=urllib.request.Request(base+'/v1/chat/completions',data=json.dumps(body).encode(),headers=headers)
 with urllib.request.urlopen(req,timeout=300) as f:d=json.load(f)
 row={'tag':tag,'wall_s':time.monotonic()-started,'usage':d.get('usage'),'timings':d.get('timings'),'finish_reason':d['choices'][0]['finish_reason']}
 rows.append(row);print(json.dumps(row),flush=True)
a.output.write_text(json.dumps({'kind':'synthetic sequential replay, not captured real OpenCode request','rows':rows},indent=2))
