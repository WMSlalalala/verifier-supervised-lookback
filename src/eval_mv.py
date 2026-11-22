"""多视角评估：同一份多视角目录，呈现 NV 个视角给 reader。
NV=1 为单视角对照，NV=3 为多视角。唯一变量是视角数。"""
import json, os, re, torch, collections, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
DIRF=os.environ.get('DIRF','directory_mv3.jsonl'); TAG=os.environ.get('TAG','mv3')
NV=int(os.environ.get('NV','3'))   # 呈现几个视角
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
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))
print(f'{TAG}: 目录条目 {len(DIR)}  视角数 NV={NV}', flush=True)
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()
def gen(p,n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()
R=[]; t0=time.time()
for k,c in enumerate(cases):
    ep,t=c['ep'],c['t']
    rows=[f"Screen {i}: {DIR[f'{ep}_{i}.png']}" for i in range(t) if DIR.get(f'{ep}_{i}.png')]
    pl=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
        f"[Index of screens you have already seen]\n"+"\n".join(rows)+
        f"\n\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
        f"On the current screen you must type something into an input field. "
        f"The value you need was visible on exactly ONE of the earlier screens.\n"
        f"Which earlier screen number contains it? Answer with ONLY the number.")
    m=re.search(r'\d+',gen(pl,8)); pred=int(m.group()) if m else -1
    ctx=f"[A screen you saw earlier]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n" if pred>=0 else ""
    pr=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
        f"{ctx}[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
        f"What exact text should you type now? Answer with ONLY that text.")
    R.append((pred==c['src'], norm(c['ans']) in norm(gen(pr,24)), c['gap'], c['src'], pred))
    if (k+1)%40==0: print(f'  {k+1}/{len(cases)}  loc={100*sum(1 for x in R if x[0])/len(R):.0f}%  {time.time()-t0:.0f}s', flush=True)
n=len(R)
print('\n'+'='*60)
print(f'{TAG} 目录  n={n}')
print(f"  定位 R@1   {100*sum(1 for x in R if x[0])/n:5.1f}%     [r0=30.5%  全历史=47.5%  oracle=55.9%]")
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
