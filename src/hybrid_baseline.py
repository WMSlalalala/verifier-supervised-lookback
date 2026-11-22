"""BM25 + LLM 混合基线（retrieve-then-rerank）

发现：BM25 只会近距离(gap1-2: 65%, gap>=3: 0-3%)，LLM 只会中距离(gap1-2: 18%, gap5-7: 71%)
     两者盲区互补 -> 简单融合可能就解决问题，必须排除这个可能

H1 BM25-top5 -> LLM 选       LLM 只看 BM25 召回的 5 屏全文（上界 = BM25 R@5 = 71.2%）
H2 BM25-top5 -> LLM 选(目录)  同上但给目录条目而非全文
H3 rank 融合                  BM25 排名与 LLM 选择加权

对照：BM25-ctx R@1=11.0  LLM全历史 R@1=47.5  BM25-oracle R@1=63.6
"""
import json, os, re, math, collections, torch, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
K=int(os.environ.get('K','5')); LIMIT=int(os.environ.get('LIMIT','0'))
def toks(s): return re.findall(r'[a-z0-9]+',(s or '').lower())
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
DIR={}
for ln in open(f'{ROOT}/directory_r0.jsonl'):
    try: d=json.loads(ln); DIR[d['img']]=d['entry']
    except Exception: pass
cases=json.load(open(f'{ROOT}/cases_clean.json'))
if LIMIT: cases=cases[:LIMIT]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))

def bm25_order(q,docs,k1=1.5,b=0.75):
    N=len(docs); dt=[toks(d) for d in docs]; df=collections.Counter()
    avg=sum(len(x) for x in dt)/max(N,1)
    for x in dt: df.update(set(x))
    out=[]
    for i,x in enumerate(dt):
        tf=collections.Counter(x); sc=0.
        for t in toks(q):
            if t in tf:
                idf=math.log(1+(N-df[t]+0.5)/(df[t]+0.5))
                sc+=idf*tf[t]*(k1+1)/(tf[t]+k1*(1-b+b*len(x)/max(avg,1)))
        out.append((sc,i))
    out.sort(key=lambda z:(-z[0],z[1])); return [i for _,i in out]

print(f'loading {MODEL} ...',flush=True); t0=time.time()
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='auto'); model.eval()
print(f'loaded in {time.time()-t0:.0f}s',flush=True)
def gen(p,n=8):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=n,
                         do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True).strip()

R=collections.defaultdict(list); recall5=[]
for k,c in enumerate(cases):
    ep,t,src=c['ep'],c['t'],c['src']
    idxs=[i for i in range(t) if OCR.get(f'{ep}_{i}.png')]
    if src not in idxs: continue
    docs=[OCR[f'{ep}_{i}.png'] for i in idxs]
    q=anno[ep]['task_info']['task']+' '+OCR.get(f'{ep}_{t}.png','')
    order=[idxs[i] for i in bm25_order(q,docs)]
    cand=order[:K]; recall5.append(src in cand)
    head=(f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n")
    tail=(f"\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
          f"On the current screen you must type something into an input field. "
          f"The value you need was visible on exactly ONE of the candidate screens above.\n"
          f"Which screen number contains it? Answer with ONLY the number.")
    # H1 全文候选
    b1="[Candidate screens]\n"+"\n".join(f"Screen {i}: {OCR[f'{ep}_{i}.png']}" for i in cand)
    m=re.search(r'\d+',gen(head+b1+tail)); p1=int(m.group()) if m else -1
    # H2 目录候选
    b2="[Candidate screens (index entries)]\n"+"\n".join(f"Screen {i}: {DIR.get(f'{ep}_{i}.png','')}" for i in cand)
    m=re.search(r'\d+',gen(head+b2+tail)); p2=int(m.group()) if m else -1
    R['H1'].append((p1==src,c['gap'])); R['H2'].append((p2==src,c['gap']))
    R['BM25@1'].append((order[0]==src,c['gap']))
    if (k+1)%25==0: print(f'  {k+1}/{len(cases)}  {time.time()-t0:.0f}s',flush=True)

n=len(R['H1'])
print('\n'+'='*66)
print(f'MODEL={MODEL}  n={n}  K={K}')
print(f"BM25 top-{K} 召回率(上界)                {100*sum(recall5)/len(recall5):5.1f}%")
print(f"BM25 R@1                               {100*sum(1 for x,_ in R['BM25@1'] if x)/n:5.1f}%")
print(f"H1 BM25-top{K} -> LLM 选(全文)           {100*sum(1 for x,_ in R['H1'] if x)/n:5.1f}%   <- 最强混合基线")
print(f"H2 BM25-top{K} -> LLM 选(目录)           {100*sum(1 for x,_ in R['H2'] if x)/n:5.1f}%")
print(f"\n对照: LLM全历史 47.5%   BM25-oracle 63.6%")
print('\n=== 按 gap ===')
print(f"{'gap':<8}{'n':>5}{'BM25':>8}{'H1':>8}{'H2':>8}")
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[i for i,(_,g) in enumerate(R['H1']) if lo<=g<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    f=lambda key:100*sum(1 for i in idx if R[key][i][0])/len(idx)
    print(f"{lab:<8}{len(idx):>5}{f('BM25@1'):>7.0f}%{f('H1'):>7.0f}%{f('H2'):>7.0f}%")
json.dump({k:v for k,v in R.items()}|{'recall5':recall5},open(f'{ROOT}/hybrid_result.json','w'))
print(f'\n-> {ROOT}/hybrid_result.json')
