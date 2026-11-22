"""[路由版] 逐屏打分并记录每屏 P(Yes)，供按距离分治的路由决策使用。
对照 eval_r1.py 的一次性选择。同一份目录、同一模型，唯一变量=选择机制。
检验 §3.15.8：oracle 69.5% 说明信息在目录中，是否一次性选择无法提取。"""
import json, os, re, torch, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
DIRF=os.environ.get('DIRF','directory_r0.jsonl'); TAG=os.environ.get('TAG','router')
NV=int(os.environ.get('NV','1'))
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
DIR={}
for ln in open(f'{ROOT}/{DIRF}'):
    try:
        d=json.loads(ln)
        es=d.get('entries') or ([d['entry']] if d.get('entry') else [])
        es=[e for e in es[:NV] if e]
        if es: DIR[d['img']]=' | '.join(es)
    except Exception: pass
cases=json.load(open(f'{ROOT}/cases_clean.json'))
VALID=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))
print(f'{TAG}: 目录 {len(DIR)}  NV={NV}  逐屏打分', flush=True)
tok=AutoTokenizer.from_pretrained(MODEL, padding_side='left')
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()
YES=[tok.encode(x,add_special_tokens=False)[0] for x in (' Yes','Yes')]
NO=[tok.encode(x,add_special_tokens=False)[0] for x in (' No','No')]

def score_prompt(c, i, entry):
    return tok.apply_chat_template([{"role":"user","content":
        f"You are operating an Android device.\n\nTask: {anno[c['ep']]['task_info']['task']}\n\n"
        f"[Current screen {c['t']}]\n{OCR.get(f'''{c['ep']}_{c['t']}.png''','')}\n\n"
        f"On the current screen you must type a value that was visible on ONE earlier screen.\n\n"
        f"[Candidate earlier screen {i}]\n{entry}\n\n"
        f"Does this earlier screen contain the value you now need? Answer Yes or No."}],
        tokenize=False, add_generation_prompt=True)

def gen(p,n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()

R=[]; t0=time.time()
for k,c in enumerate(cases):
    ep,t=c['ep'],c['t']
    scr=[(i,DIR[f'{ep}_{i}.png']) for i in range(t) if DIR.get(f'{ep}_{i}.png')]
    if not scr: R.append((False,False,c['gap'],c['src'],-1)); continue
    prompts=[score_prompt(c,i,e) for i,e in scr]
    scores=[]
    B=8
    for b in range(0,len(prompts),B):
        enc=tok(prompts[b:b+B],return_tensors='pt',padding=True,truncation=True,max_length=1536).to(model.device)
        with torch.no_grad():
            lg=model(**enc).logits[:,-1,:].float()
        pr=torch.softmax(lg,dim=-1)
        for row in pr:
            py=sum(row[j].item() for j in YES); pn=sum(row[j].item() for j in NO)
            scores.append(py/(py+pn+1e-9))
    order=sorted(range(len(scores)),key=lambda j:-scores[j])
    pred=scr[order[0]][0]
    top1=scores[order[0]]
    top2=scores[order[1]] if len(scores)>1 else 0.0
    import math as _m
    ssum=sum(scores)+1e-9
    ent=-sum((v/ssum)*_m.log((v/ssum)+1e-12) for v in scores)/_m.log(max(len(scores),2))
    ctx=f"[A screen you saw earlier]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n"
    pr_=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
         f"{ctx}[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
         f"What exact text should you type now? Answer with ONLY that text.")
    R.append((pred in VALID[k], norm(c['ans']) in norm(gen(pr_,24)), c['gap'], c['src'], pred,
              {'top1':top1,'top2':top2,'margin':top1-top2,'entropy':ent,
               'nscr':len(scores),'scores':[round(v,4) for v in scores],
               'screens':[i for i,_ in scr]}))
    if (k+1)%20==0: print(f'  {k+1}/{len(cases)}  loc={100*sum(1 for x in R if x[0])/len(R):.0f}%  {time.time()-t0:.0f}s', flush=True)
n=len(R)
print('\n'+'='*60)
print(f'{TAG}  n={n}  (定位已用修正指标)')
print(f"  定位 R@1   {100*sum(1 for x in R if x[0])/n:5.1f}%     [r0单阶段=45.8%  全历史=56.8%  oracle=69.5%]")
print(f"  端到端     {100*sum(1 for x in R if x[1])/n:5.1f}%     [r0(E)=22.9%  全历史=39.8%]")
print('\n=== 按 gap ===')
print(f"{'gap':<8}{'n':>5}{'定位':>8}{'端到端':>9}")
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[x for x in R if lo<=x[2]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}{100*sum(1 for x in idx if x[0])/len(idx):>7.0f}%{100*sum(1 for x in idx if x[1])/len(idx):>8.0f}%")
json.dump(R, open(f'{ROOT}/eval_{TAG}_result.json','w'))
print(f'\n-> {ROOT}/eval_{TAG}_result.json')
