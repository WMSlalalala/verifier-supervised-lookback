"""校准两段式离线分析：s1>=τ 用 p1 否则 p2。τ 在 5-fold CV 训练折选；报告 CV 准确率、gap 1-2 修复情况、vs B/D 配对。"""
import json, math, random
ROOT='/mnt/share/mwang49/guiodyssey'
C=json.load(open(f'{ROOT}/cases_long.json')); V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens_long.json'))]
R=json.load(open(f'{ROOT}/eval_long_C2_result.json')); N=len(R)
B=json.load(open(f'{ROOT}/eval_long_B_result.json')); D=json.load(open(f'{ROOT}/eval_long_D_result.json'))
ok_b=[x[0] for x in B]; ok_d=[x[0] for x in D]
s1=[x[8]['s1'] for x in R]; ok1=[x[8]['ok1'] for x in R]; ok2=[x[8]['ok2'] for x in R]
def route(idx,t): return [ (ok1[i] if s1[i]>=t else ok2[i]) for i in idx]
def acc(v): return 100*sum(v)/max(len(v),1)
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
print(f'n={N}')
print(f'第一段单独（总用 p1）: {acc(ok1):.1f}%   第二段单独（总用 p2）: {acc(ok2):.1f}%   B {acc(ok_b):.1f}%  D {acc(ok_d):.1f}%')
print(f'oracle(两段任一对): {100*sum(1 for i in range(N) if ok1[i] or ok2[i])/N:.1f}%')
near=[i for i in range(N) if C[i]['gap']<=2]; far=[i for i in range(N) if C[i]['gap']>2]
print(f'\ns1 分布：gap<=2 中位 {sorted(s1[i] for i in near)[len(near)//2]:.3f}   gap>2 中位 {sorted(s1[i] for i in far)[len(far)//2]:.3f}')
print(f'第一段在 gap<=2 上的命中: {acc([ok1[i] for i in near]):.0f}%  (B 0%, D 13%)')
print('\n=== τ 扫描（全量，过拟合参考）===')
for t in (0.3,0.5,0.6,0.7,0.8,0.9,0.95,0.99):
    r=route(range(N),t); fire=sum(1 for i in range(N) if s1[i]>=t)
    print(f'  τ={t:<5} 触发 {fire:>3}/{N}  总体 {acc(r):5.1f}%  gap1-2 {acc([r[i] for i in near]):4.0f}%  gap>2 {acc([r[i] for i in far]):4.0f}%')
print('\n=== 5-fold CV（τ 仅在训练折选）===')
random.seed(0); order=list(range(N)); random.shuffle(order); folds=[order[i::5] for i in range(5)]
cand=sorted(set(s1)); cv=[None]*N
for f in range(5):
    test=folds[f]; train=[i for i in order if i not in set(test)]
    best=max(cand,key=lambda t:sum(route(train,t)))
    for i,v in zip(test,route(test,best)): cv[i]=v
print(f'  CV 准确率 {acc(cv):.1f}%   gap1-2 {acc([cv[i] for i in near]):.0f}%   gap>2 {acc([cv[i] for i in far]):.0f}%')
for nm,base in (('B 全历史',ok_b),('D 索引',ok_d)):
    d,p=mc(base,cv); print(f'  CV路由 vs {nm}: 净{d:+3d}  p={p:.4f}{" 显著" if p<0.05 else ""}')
d,p=mc([ok_b[i] for i in near],[cv[i] for i in near]); print(f'  gap1-2 子集 CV路由 vs B: 净{d:+3d} p={p:.4f}{" 显著" if p<0.05 else ""}')
d,p=mc([ok_d[i] for i in near],[cv[i] for i in near]); print(f'  gap1-2 子集 CV路由 vs D: 净{d:+3d} p={p:.4f}{" 显著" if p<0.05 else ""}')
