"""端到端：对 scorer_eval_rows 中每个 case，用 14B 读取打分器选出的屏（与 E/门控同一 read prompt），给出端到端正确率。"""
import json,os,re,torch,time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'; MODEL='Qwen/Qwen2.5-14B-Instruct'; SRC=os.environ.get('SRC','trained')   # trained | untrained
HIST=os.environ.get('HIST','0')=='1'   # 1: 读取时附带全历史，所选屏置于当前屏之前
MARK=os.environ.get('MARK','scorer')   # scorer | gold | recent | random  （HIST=1 时标哪一屏）
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
SET=os.environ.get('SET',''); PREFIX=os.environ.get('PREFIX','scorer')
cases=json.load(open(f'{ROOT}/scorer_cases{SET}.json'))
probs={}
if SRC=='trained' and SET=='':
    for f in range(5):
        for k,v in json.load(open(f'{ROOT}/{PREFIX}_fold{f}_probs.json')).items(): probs[int(k)]={int(i):x for i,x in v.items()}
elif SRC=='trained':
    for k,v in json.load(open(f'{ROOT}/{PREFIX}_foldext_probs.json')).items(): probs[int(k)]={int(i):x for i,x in v.items()}
else:
    for k,v in json.load(open(f'{ROOT}/scorer_untrained{SET}_probs.json')).items(): probs[int(k)]={int(i):x for i,x in v.items()}
OFF=(188 if (SET=='_more' and SRC=='trained') else 0)
tok=AutoTokenizer.from_pretrained(MODEL)
_mm=os.environ.get('MAXMEM'); _kw={'max_memory':{int(k):v for k,v in json.loads(_mm).items()}} if _mm else {}
model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='auto',**_kw); model.eval()
def gen(p,n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad(): o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()
out=[]; t0=time.time()
for ci,c in enumerate(cases):
    pr=probs[ci+OFF]; pred=max(pr,key=pr.get); ep,t=c['ep'],c['t']
    if MARK=='gold': pred=max(c['valid'])
    elif MARK=='recent': pred=max(i for i in range(t) if OCR.get(f'{ep}_{i}.png'))
    elif MARK=='random':
        import random; random.seed(ci); pred=random.choice([i for i in range(t) if OCR.get(f'{ep}_{i}.png')])
    if HIST:
        hist=''.join(f"Screen {i}: {OCR.get(f'{ep}_{i}.png','')}\n" for i in range(t) if OCR.get(f'{ep}_{i}.png'))
        if MARK=='top2':
            top=sorted(pr,key=pr.get,reverse=True)[:2]
            mk=''.join(f"Screen {j}: {OCR.get(f'{ep}_{j}.png','')}\n" for j in top)
            ctx=f"[All screens you saw earlier]\n{hist}\n[The two earlier screens most likely to hold the value you need now]\n{mk}\n"
        else:
            ctx=f"[All screens you saw earlier]\n{hist}\n[The earlier screen most likely to hold the value you need now]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n"
    else:
        ctx=f"[A screen you saw earlier]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n"
    p=(f"You are operating an Android device.\n\nTask: {c['task']}\n\n{ctx}[Current screen {t}]\n{c['cur']}\n\nWhat exact text should you type now? Answer with ONLY that text.")
    ok=norm(c['ans']) in norm(gen(p)); out.append(dict(case=ci,set=c['set'],t=t,gap=c['gap'],pred=pred,loc=pred in c['valid'],e2e=ok))
    if (ci+1)%40==0: print(f'{ci+1}/{len(cases)} {time.time()-t0:.0f}s',flush=True)
json.dump(out,open(f'{ROOT}/{PREFIX}_{SRC}{SET}{"_hist" if HIST else ""}{"" if MARK=="scorer" else "_"+MARK}_e2e.json','w'))
n=len(out); print(f"{SRC}: 定位 {100*sum(o['loc'] for o in out)/n:.1f}%  端到端 {100*sum(o['e2e'] for o in out)/n:.1f}%  (n={n})")
for s in ('short','long','holdout'):
    r=[o for o in out if o['set']==s]
    if r: print(f"  {s:<8} n={len(r)} 定位 {100*sum(o['loc'] for o in r)/len(r):.1f} 端到端 {100*sum(o['e2e'] for o in r)/len(r):.1f}")
print('READ DONE')
