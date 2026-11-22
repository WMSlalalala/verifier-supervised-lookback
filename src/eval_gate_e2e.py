"""diff 门控方法的端到端评估：固定 τ 选屏 -> 读取该屏原文作答。CASES=long|short|holdout；MODEL 可换。"""
import json,os,re,torch,time,math
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'; CASES=os.environ.get('CASES','long'); TAU=float(os.environ.get('TAU','0.1'))
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct'); MS=('' if '14B' in MODEL else '_'+MODEL.split('/')[-1].split('-')[1])
TAG=f'{CASES}_GATE{MS}'
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())
def toks(s): return set(re.findall(r'[a-z0-9]{3,}',(s or '').lower()))
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cf={'long':'cases_long.json','short':'cases_clean.json','holdout':'cases_holdout.json'}[CASES]
vf={'long':'valid_screens_long.json','short':'valid_screens.json','holdout':'valid_screens_holdout.json'}[CASES]
cases=json.load(open(f'{ROOT}/{cf}')); VALID=[set(v) for v in json.load(open(f'{ROOT}/{vf}'))]
C2=json.load(open(f'{ROOT}/eval_{CASES}_C2{MS}_result.json')); assert len(C2)==len(cases)
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))
tok=AutoTokenizer.from_pretrained(MODEL)
_mm=os.environ.get('MAXMEM'); _kw={'max_memory':{int(k):v for k,v in json.loads(_mm).items()}} if _mm else {}
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto', **_kw); model.eval()
def gen(p,n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad(): o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()
PART=f'{ROOT}/eval_{TAG}_partial.jsonl'; done={}
if os.path.exists(PART):
    for ln in open(PART):
        try: d=json.loads(ln); done[d['k']]=d['r']
        except Exception: pass
pf=open(PART,'a'); R=[None]*len(cases); t0=time.time()
print(f'{TAG}: τ={TAU} n={len(cases)} 断点 {len(done)}', flush=True)
for k,c in enumerate(cases):
    if k in done: R[k]=tuple(done[k]); continue
    ep,t=c['ep'],c['t']; cur=toks(OCR.get(f'{ep}_{t}.png',''))
    rec=[toks(OCR.get(f'{ep}_{j}.png','')) for j in range(max(0,t-2),t)]
    old=[toks(OCR.get(f'{ep}_{j}.png','')) for j in range(0,max(0,t-2)) if OCR.get(f'{ep}_{j}.png')]
    diff=max((len(cur&r)/max(len(cur|r),1) for r in rec),default=0)-max((len(cur&r)/max(len(cur|r),1) for r in old),default=0)
    x=C2[k][8]; pred=x['p1'] if diff>=TAU else x['p2']; stage=1 if diff>=TAU else 2
    ctx=f"[A screen you saw earlier]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n" if pred>=0 else ""
    pr=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n{ctx}[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
        f"What exact text should you type now? Answer with ONLY that text.")
    R[k]=(pred in VALID[k], norm(c['ans']) in norm(gen(pr,24)), c['gap'], c['src'], pred, stage, t, round(diff,4))
    pf.write(json.dumps({'k':k,'r':list(R[k])})+'\n'); pf.flush()
    if (k+1)%40==0: print(f'  {k+1}/{len(cases)} {time.time()-t0:.0f}s', flush=True)
pf.close(); n=len(R)
print(f'\n{TAG}  n={n}  定位 {100*sum(1 for x in R if x[0])/n:.1f}%  端到端 {100*sum(1 for x in R if x[1])/n:.1f}%  第一段触发 {100*sum(1 for x in R if x[5]==1)/n:.0f}%')
for lo,hi in [(1,2),(3,7),(8,12),(13,99)]:
    idx=[x for x in R if lo<=x[2]<=hi]
    if idx: print(f"  gap {lo}-{hi if hi<99 else '+'}: n={len(idx)} 定位 {100*sum(1 for x in idx if x[0])/len(idx):.0f}% 端到端 {100*sum(1 for x in idx if x[1])/len(idx):.0f}%")
json.dump(R,open(f'{ROOT}/eval_{TAG}_result.json','w')); print(f'-> eval_{TAG}_result.json')
