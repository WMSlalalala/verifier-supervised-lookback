"""长轨迹 B(全历史) vs D(目录) 配对分析：总体 + 按 t 分桶 + 按 gap，McNemar；并与短轨迹 118 case 对照。"""
import json, math, statistics, os
ROOT='/mnt/share/mwang49/guiodyssey'
B=json.load(open(f'{ROOT}/eval_long_B_result.json')); D=json.load(open(f'{ROOT}/eval_long_D_result.json'))
cases=json.load(open(f'{ROOT}/cases_long.json')); N=len(cases); assert len(B)==len(D)==N
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
def pct(v): return 100*sum(v)/max(len(v),1)
lb=[x[0] for x in B]; ld=[x[0] for x in D]; eb=[x[1] for x in B]; ed=[x[1] for x in D]
print(f'=== 长轨迹 n={N}  t 中位 {statistics.median(c["t"] for c in cases)}  gap 中位 {statistics.median(c["gap"] for c in cases)} ===')
print(f"{'':<10}{'全历史B':>9}{'目录D':>8}{'D-B':>7}{'p':>9}")
d,p=mc(lb,ld); print(f"{'定位':<10}{pct(lb):>8.1f}%{pct(ld):>7.1f}%{pct(ld)-pct(lb):>+7.1f}{p:>9.4f} {'显著' if p<0.05 else ''}")
d,p=mc(eb,ed); print(f"{'端到端':<10}{pct(eb):>8.1f}%{pct(ed):>7.1f}%{pct(ed)-pct(eb):>+7.1f}{p:>9.4f} {'显著' if p<0.05 else ''}")
print('\n=== 按轨迹长度 t（定位）===')
print(f"{'t':<8}{'n':>4}{'全历史':>8}{'目录':>7}{'D-B':>7}{'p':>9}")
for lo,hi in [(16,19),(20,24),(25,29),(30,999)]:
    idx=[i for i in range(N) if lo<=cases[i]['t']<=hi]
    if not idx: continue
    a=[lb[i] for i in idx]; b=[ld[i] for i in idx]; d,p=mc(a,b)
    lab=f'{lo}-{hi}' if hi<999 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>4}{pct(a):>7.0f}%{pct(b):>6.0f}%{pct(b)-pct(a):>+7.0f}{p:>9.4f} {'显著' if p<0.05 else ''}")
print('\n=== 按 gap（定位）===')
for lo,hi in [(1,2),(3,4),(5,7),(8,12),(13,999)]:
    idx=[i for i in range(N) if lo<=cases[i]['gap']<=hi]
    if not idx: continue
    a=[lb[i] for i in idx]; b=[ld[i] for i in idx]; d,p=mc(a,b)
    lab=f'{lo}-{hi}' if hi<999 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>4}{pct(a):>7.0f}%{pct(b):>6.0f}%{pct(b)-pct(a):>+7.0f}{p:>9.4f} {'显著' if p<0.05 else ''}")
# 与短轨迹对照
V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json')))
keep=[i for i in range(127) if i not in bad]; cs=json.load(open(f'{ROOT}/cases_clean.json'))
sb=[m['B'][i][4] in V[k] for k,i in enumerate(keep)]; sd=[m['D'][i][4] in V[k] for k,i in enumerate(keep)]
print('\n=== 短轨迹(118) vs 长轨迹 合并趋势（定位）===')
print(f"{'t':<8}{'n':>4}{'全历史':>8}{'目录':>7}{'D-B':>7}")
allc=[(cs[k]['t'],sb[k],sd[k]) for k in range(118)]+[(cases[i]['t'],lb[i],ld[i]) for i in range(N)]
for lo,hi in [(1,7),(8,11),(12,15),(16,19),(20,24),(25,29),(30,999)]:
    idx=[x for x in allc if lo<=x[0]<=hi]
    if not idx: continue
    a=pct([x[1] for x in idx]); b=pct([x[2] for x in idx])
    lab=f'{lo}-{hi}' if hi<999 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>4}{a:>7.0f}%{b:>6.0f}%{b-a:>+7.0f}")
