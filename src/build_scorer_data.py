"""验证器监督的逐屏打分器：构建 (case, 历史屏 i) 对 + 按轨迹分 5 折。标签 = i ∈ valid_screens（自动验证器给出，无人标注）"""
import json,random,os
ROOT='/mnt/share/mwang49/guiodyssey'
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
sets=[('short','cases_clean.json','valid_screens.json','clean_idx_short.json'),('long','cases_long.json','valid_screens_long.json','clean_idx_long.json'),('holdout','cases_holdout.json','valid_screens_holdout.json',None)]
cases=[]
for nm,cf,vf,idxf in sets:
    C=json.load(open(f'{ROOT}/{cf}')); V=json.load(open(f'{ROOT}/{vf}')); I=json.load(open(f'{ROOT}/{idxf}')) if idxf else list(range(len(C)))
    for k in I: cases.append(dict(set=nm,k=k,ep=C[k]['ep'],t=C[k]['t'],gap=C[k]['gap'],ans=C[k]['ans'],valid=sorted(V[k])))
eps=sorted(set(c['ep'] for c in cases)); random.seed(0); random.shuffle(eps); fold={e:i%5 for i,e in enumerate(eps)}
anno={}
pairs=[]; 
for ci,c in enumerate(cases):
    ep=c['ep']; 
    if ep not in anno: anno[ep]=json.load(open(f'{ROOT}/annotations/{ep}.json'))['task_info'].get('task','')
    c['fold']=fold[ep]; c['task']=anno[ep]; c['cur']=OCR.get(f'{ep}_{c["t"]}.png','')
    for i in range(c['t']):
        txt=OCR.get(f'{ep}_{i}.png')
        if not txt: continue
        pairs.append(dict(case=ci,i=i,label=int(i in c['valid']),fold=c['fold']))
json.dump(cases,open(f'{ROOT}/scorer_cases.json','w')); json.dump(pairs,open(f'{ROOT}/scorer_pairs.json','w'))
from collections import Counter
print(f'cases {len(cases)} ({Counter(c["set"] for c in cases)})  pairs {len(pairs)}  正 {sum(p["label"] for p in pairs)}  折大小 {Counter(c["fold"] for c in cases)}')
