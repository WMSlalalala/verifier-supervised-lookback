"""diff 门控（纯文本，无 LLM）CV 分析，CASES=long|short。对照：B 全历史 / D(E) 索引。"""
import json,math,random,re,os
ROOT='/mnt/share/mwang49/guiodyssey'; CASES=os.environ.get('CASES','long'); MS=os.environ.get('MSUF','')
if CASES=='holdout':
    C=json.load(open(f'{ROOT}/cases_holdout.json')); R=json.load(open(f'{ROOT}/eval_holdout_C2'+MS+'_result.json'))
    B=[x[0] for x in json.load(open(f'{ROOT}/eval_holdout_B'+MS+'_result.json'))]; D=[x[0] for x in json.load(open(f'{ROOT}/eval_holdout_D'+MS+'_result.json'))]; DN='D 索引'
elif CASES=='long':
    C=json.load(open(f'{ROOT}/cases_long.json')); R=json.load(open(f'{ROOT}/eval_long_C2'+MS+'_result.json'))
    B=[x[0] for x in json.load(open(f'{ROOT}/eval_long_B'+MS+'_result.json'))]; D=[x[0] for x in json.load(open(f'{ROOT}/eval_long_D'+MS+'_result.json'))]; DN='D 索引'
else:
    C=json.load(open(f'{ROOT}/cases_clean.json')); R=json.load(open(f'{ROOT}/eval_short_C2'+MS+'_result.json'))
    V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
    m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json'))); keep=[i for i in range(127) if i not in bad]
    B=[m['B'][i][4] in V[k] for k,i in enumerate(keep)]; D=[m['E'][i][4] in V[k] for k,i in enumerate(keep)]; DN='E 索引'
N=len(R); assert len(C)==N==len(B)==len(D)
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
def toks(s): return set(re.findall(r'[a-z0-9]{3,}',(s or '').lower()))
ok1=[x[8]['ok1'] for x in R]; ok2=[x[8]['ok2'] for x in R]
diff=[]
for i,c in enumerate(C):
    ep,t=c['ep'],c['t']; cur=toks(OCR.get(f'{ep}_{t}.png',''))
    rec=[toks(OCR.get(f'{ep}_{j}.png','')) for j in range(max(0,t-2),t)]
    old=[toks(OCR.get(f'{ep}_{j}.png','')) for j in range(0,max(0,t-2)) if OCR.get(f'{ep}_{j}.png')]
    jac=max((len(cur&r)/max(len(cur|r),1) for r in rec),default=0); jo=max((len(cur&r)/max(len(cur|r),1) for r in old),default=0)
    diff.append(jac-jo)
def pct(v): return 100*sum(v)/max(len(v),1)
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
near=[i for i in range(N) if C[i]['gap']<=2]; far=[i for i in range(N) if C[i]['gap']>2]
print(f'[{CASES}] n={N}  第一段单独 {pct(ok1):.1f}%  第二段单独 {pct(ok2):.1f}%  任一对 {100*sum(1 for i in range(N) if ok1[i] or ok2[i])/N:.1f}%   B {pct(B):.1f}%  {DN} {pct(D):.1f}%')
random.seed(0); order=list(range(N)); random.shuffle(order); folds=[order[i::5] for i in range(5)]
cv=[None]*N; ths=[]
for f in range(5):
    test=folds[f]; tr=[i for i in order if i not in set(test)]
    cand=sorted(set(diff[i] for i in tr)); best=max(cand,key=lambda th:sum((ok1[i] if diff[i]>=th else ok2[i]) for i in tr)); ths.append(round(best,3))
    for i in test: cv[i]=ok1[i] if diff[i]>=best else ok2[i]
d1,p1=mc(B,cv); d2,p2=mc(D,cv)
print(f'diff 门控 5-fold CV: 总体 {pct(cv):.1f}%  gap1-2 {pct([cv[i] for i in near]):.0f}%  gap>2 {pct([cv[i] for i in far]):.0f}%   vs B 净{d1:+d} p={p1:.4f}   vs {DN} 净{d2:+d} p={p2:.4f}   各折τ {ths}')
TH=0.1; fx=[ok1[i] if diff[i]>=TH else ok2[i] for i in range(N)]; g=[diff[i]>=TH for i in range(N)]
d1,p1=mc(B,fx); d2,p2=mc(D,fx)
print(f'固定 τ=0.1（长轨迹选出的阈值，跨集迁移）: 总体 {pct(fx):.1f}%  gap1-2 {pct([fx[i] for i in near]):.0f}%  触发 {sum(g)}/{N}  近触发 {sum(g[i] for i in near)}/{len(near)}  远误触发 {sum(g[i] for i in far)}/{len(far)}   vs B 净{d1:+d} p={p1:.4f}   vs {DN} 净{d2:+d} p={p2:.4f}')
