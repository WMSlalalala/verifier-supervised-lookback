"""长轨迹评估：MODE=B 全历史原文 / MODE=D 目录条目。定位用修正指标(valid_screens_long)。
检验 §3.17.4：长上下文下全历史是否退化、索引是否不退化。"""
import json, os, re, torch, collections, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
CASES=os.environ.get('CASES','long')
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct'); MSUF=('' if '14B' in MODEL else '_'+MODEL.split('/')[-1].split('-')[1])
DIRF=os.environ.get('DIRF','directory_r0.jsonl'); MODE=os.environ.get('MODE','D'); TAG=f'{CASES}_{MODE}'+MSUF
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
DIR={}
for ln in open(f'{ROOT}/{DIRF}'):
    try: d=json.loads(ln); DIR[d['img']]=d['entry']
    except Exception: pass
cases=json.load(open(f'{ROOT}/cases_{CASES}.json'))
VALID=[set(v) for v in json.load(open(f'{ROOT}/valid_screens_{CASES}.json'))]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))
print(f'{TAG}: MODE={MODE}  cases={len(cases)}  目录条目 {len(DIR)}', flush=True)
tok=AutoTokenizer.from_pretrained(MODEL)
_mm=os.environ.get('MAXMEM')   # 例: '{"0":"11GiB","1":"22GiB"}' 每卡硬上限，避免挤爆他人任务
_kw={'max_memory':{int(k):v for k,v in json.loads(_mm).items()}} if _mm else {}
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto', **_kw); model.eval()
print('device_map:', {k:str(v) for k,v in list(model.hf_device_map.items())[:3]}, '...', flush=True)
def gen(p,n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()
PART=f'{ROOT}/eval_{TAG}_partial.jsonl'
done={}
if os.path.exists(PART):
    for ln in open(PART):
        try: d=json.loads(ln); done[d['k']]=d['r']
        except Exception: pass
print(f'断点续传: 已完成 {len(done)}/{len(cases)}', flush=True)
pf=open(PART,'a')
R=[None]*len(cases); t0=time.time()
for k,c in enumerate(cases):
    if k in done: R[k]=tuple(done[k]); continue
    ep,t=c['ep'],c['t']
    SRC = OCR if MODE=='B' else DIR
    rows=[f"Screen {i}: {SRC[f'{ep}_{i}.png']}" for i in range(t) if SRC.get(f'{ep}_{i}.png')]
    pl=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
        f"[Screens you have already seen]\n"+"\n".join(rows)+
        f"\n\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
        f"On the current screen you must type something into an input field. "
        f"The value you need was visible on exactly ONE of the earlier screens.\n"
        f"Which earlier screen number contains it? Answer with ONLY the number.")
    m=re.search(r'\d+',gen(pl,8)); pred=int(m.group()) if m else -1
    ctx=f"[A screen you saw earlier]\nScreen {pred}: {OCR.get(f'{ep}_{pred}.png','')}\n\n" if pred>=0 else ""
    pr=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
        f"{ctx}[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
        f"What exact text should you type now? Answer with ONLY that text.")
    R[k]=(pred in VALID[k], norm(c['ans']) in norm(gen(pr,24)), c['gap'], c['src'], pred, pred==c['src'], t)
    pf.write(json.dumps({'k':k,'r':list(R[k])})+'\n'); pf.flush()
    torch.cuda.empty_cache()
    if (k+1)%20==0:
        dn=[x for x in R if x is not None]
        print(f'  {k+1}/{len(cases)}  loc={100*sum(1 for x in dn if x[0])/len(dn):.0f}%  {time.time()-t0:.0f}s', flush=True)
pf.close()
assert all(x is not None for x in R)
n=len(R)
print('\n'+'='*60)
print(f'{TAG}  n={n}  (定位=修正指标)')
print(f"  定位 R@1   {100*sum(1 for x in R if x[0])/n:5.1f}%   (严格 {100*sum(1 for x in R if x[5])/n:.1f}%)")
print(f"  端到端     {100*sum(1 for x in R if x[1])/n:5.1f}%")
print('\n=== 按轨迹长度 t ===')
print(f"{'t':<8}{'n':>5}{'定位':>8}{'端到端':>9}")
for lo,hi in [(16,19),(20,24),(25,29),(30,999)]:
    idx=[x for x in R if lo<=x[6]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<999 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}{100*sum(1 for x in idx if x[0])/len(idx):>7.0f}%{100*sum(1 for x in idx if x[1])/len(idx):>8.0f}%")
print('\n=== 按 gap ===')
for lo,hi in [(1,2),(3,4),(5,7),(8,12),(13,999)]:
    idx=[x for x in R if lo<=x[2]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<999 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}{100*sum(1 for x in idx if x[0])/len(idx):>7.0f}%{100*sum(1 for x in idx if x[1])/len(idx):>8.0f}%")
json.dump(R, open(f'{ROOT}/eval_{TAG}_result.json','w'))
print(f'\n-> {ROOT}/eval_{TAG}_result.json')
