"""汇总 5 折打分 -> 定位；与 B / E / 未训练打分器 配对比较，按集合与 t 分解。"""
import json,math,os
ROOT='/mnt/share/mwang49/guiodyssey'
cases=json.load(open(f'{ROOT}/scorer_cases.json'))
probs={}
for f in range(5):
    p=f'{ROOT}/{os.environ.get("PREFIX","scorer")}_fold{f}_probs.json'
    if os.path.exists(p):
        for k,v in json.load(open(p)).items(): probs[int(k)]={int(i):x for i,x in v.items()}
unt=json.load(open(f'{ROOT}/scorer_untrained_probs.json')) if os.path.exists(f'{ROOT}/scorer_untrained_probs.json') else {}
def pct(v): return 100*sum(v)/max(len(v),1)
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
# 基线：B / 索引 的定位（干净口径）
V={'short':[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))],'long':[set(v) for v in json.load(open(f'{ROOT}/valid_screens_long.json'))],'holdout':[set(v) for v in json.load(open(f'{ROOT}/valid_screens_holdout.json'))]}
m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json'))); keep=[i for i in range(127) if i not in bad]
BL=json.load(open(f'{ROOT}/eval_long_B_result.json')); DL=json.load(open(f'{ROOT}/eval_long_D_result.json')); BH=json.load(open(f'{ROOT}/eval_holdout_B_result.json')); DH=json.load(open(f'{ROOT}/eval_holdout_D_result.json'))
rows=[]
for ci,c in enumerate(cases):
    k=c['k']; s=c['set']
    if s=='short': b=m['B'][keep[k]][4] in V[s][k]; e=m['E'][keep[k]][4] in V[s][k]
    elif s=='long': b=BL[k][0]; e=DL[k][0]
    else: b=BH[k][0]; e=DH[k][0]
    pr=probs.get(ci); pu=unt.get(str(ci))
    sc=(max(pr,key=pr.get) in c['valid']) if pr else None
    su=(int(max(pu,key=pu.get)) in c['valid']) if pu else None
    rows.append(dict(set=s,t=c['t'],gap=c['gap'],B=b,E=e,S=sc,U=su,pmax=max(pr.values()) if pr else None))
have=[r for r in rows if r['S'] is not None]; print(f'已打分 case {len(have)}/{len(rows)}')
def report(lab,rs):
    if not rs: return
    S=[r['S'] for r in rs]; B=[r['B'] for r in rs]; E=[r['E'] for r in rs]
    d1,p1=mc(B,S); d2,p2=mc(E,S); line=f"{lab:<22} n={len(rs):<4} B {pct(B):5.1f}  索引 {pct(E):5.1f}  打分器 {pct(S):5.1f}   vs B 净{d1:+d} p={p1:.3f}   vs 索引 净{d2:+d} p={p2:.3f}"
    if all(r['U'] is not None for r in rs): U=[r['U'] for r in rs]; d3,p3=mc(U,S); line+=f"   未训练 {pct(U):5.1f} (净{d3:+d} p={p3:.3f})"
    print(line)
report('全部',have)
for s in ('short','long','holdout'): report(s,[r for r in have if r['set']==s])
report('t<=15',[r for r in have if r['t']<=15]); report('t>=16',[r for r in have if r['t']>=16]); report('t>=20',[r for r in have if r['t']>=20])
for lo,hi in [(1,2),(3,4),(5,7),(8,12),(13,99)]: report(f'gap {lo}-{hi if hi<99 else "+"}',[r for r in have if lo<=r['gap']<=hi])
json.dump(rows,open(f'{ROOT}/scorer_eval_rows.json','w'))
