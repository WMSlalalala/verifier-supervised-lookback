"""最终汇总：主结果 / 训练过的全历史基线 / 消融 / top2 / 外部集。缺文件自动跳过。"""
import json,math,os
ROOT='/mnt/share/mwang49/guiodyssey'
def L(p): 
    p=f'{ROOT}/{p}'; return json.load(open(p)) if os.path.exists(p) else None
def pct(v): return 100*sum(v)/max(len(v),1)
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
cases=L('scorer_cases.json')
def load_probs(prefix):
    pr={}; nf=0
    for f in range(5):
        d=L(f'{prefix}_fold{f}_probs.json')
        if d is None: continue
        nf+=1
        for k,v in d.items(): pr[int(k)]={int(i):x for i,x in v.items()}
    return (pr,nf) if pr else (None,0)
def loc_of(pr):
    return [ (max(pr[i],key=pr[i].get) in cases[i]['valid']) if i in pr else None for i in range(len(cases)) ]
rows_loc=L('scorer_eval_rows.json'); rows_e2e=L('scorer_e2e_rows.json')
B=[r['B'] for r in rows_loc]; E=[r['E'] for r in rows_loc]
Be=[r['B'] for r in rows_e2e]; Ee=[r['E'] for r in rows_e2e]
BASE,_=load_probs('scorer')
BASE=loc_of(BASE)
print('='*96); print('① 主结果 + 训练过的全历史基线 + 消融（定位，n=%d，五折）'%len(cases))
variants=[('look-back 打分器(ours)','scorer'),('训练过的全历史(同标签 SFT)','fullhist'),('消融: 去掉距离','scorer_nodist'),('消融: 正例权重=1','scorer_posw1'),('消融: 3B 模型','scorer_3B')]
import collections
sub={'all':list(range(len(cases))),'t<=15':[i for i,c in enumerate(cases) if c['t']<=15],'t>=16':[i for i,c in enumerate(cases) if c['t']>=16],'t>=20':[i for i,c in enumerate(cases) if c['t']>=20]}
hdr=f"{'方法':<26}"+''.join(f"{k:>9}" for k in sub)+"   vs B(all)        vs 打分器(all)"
print(hdr)
print(f"{'全历史 B (prompt, 定位)':<26}"+''.join(f"{pct([B[i] for i in idx]):>8.1f}%" for idx in sub.values()))
print(f"{'屏幕索引 E (prompt)':<26}"+''.join(f"{pct([E[i] for i in idx]):>8.1f}%" for idx in sub.values()))
U=L('scorer_untrained_probs.json')
if U:
    up={int(k):{int(i):x for i,x in v.items()} for k,v in U.items()}; UL=loc_of(up)
    print(f"{'未训练打分器':<26}"+''.join(f"{pct([UL[i] for i in idx]):>8.1f}%" for idx in sub.values()))
for nm,pfx in variants:
    pr,nf=load_probs(pfx)
    if not pr: print(f"{nm:<26}  (未开始)"); continue
    nm=nm if nf==5 else f'{nm}[{nf}折]'
    lo=loc_of(pr); ok=[i for i in range(len(cases)) if lo[i] is not None]
    line=f"{nm:<26}"+''.join(f"{pct([lo[i] for i in idx if lo[i] is not None]):>8.1f}%" for idx in sub.values())
    d1,p1=mc([B[i] for i in ok],[lo[i] for i in ok]); d2,p2=mc([BASE[i] for i in ok],[lo[i] for i in ok])
    line+=f"   净{d1:+d} p={p1:.3f}"+("" if pfx=='scorer' else f"   净{d2:+d} p={p2:.3f}")
    print(line)
# ② top2
T=L('scorer_trained_hist_e2e.json'); T2=L('scorer_trained_hist_top2_e2e.json')
if T2:
    print('='*96); print('② 读取时标注 top-1 vs top-2（端到端）')
    a=[o['e2e'] for o in T]; b=[o['e2e'] for o in T2]
    for k,idx in sub.items():
        d,p=mc([a[i] for i in idx],[b[i] for i in idx])
        print(f"  {k:<8} n={len(idx):<4} top1 {pct([a[i] for i in idx]):5.1f}  top2 {pct([b[i] for i in idx]):5.1f}   净{d:+d} p={p:.3f}")
# ③ 外部集
CM=L('cases_more.json')
if CM and L('scorer_foldext_probs.json'):
    cm=L('scorer_cases_more.json'); pr={int(k):{int(i):x for i,x in v.items()} for k,v in L('scorer_foldext_probs.json').items()}
    off=len(cases); lo=[(max(pr[i+off],key=pr[i+off].get) in cm[i]['valid']) if (i+off) in pr else None for i in range(len(cm))]
    ok=[i for i in range(len(cm)) if lo[i] is not None]
    print('='*96); print(f'③ 外部测试集（第四批轨迹，用全部 {len(cases)} case 训练，一次评估） n={len(ok)}')
    Bm=L('eval_more_B_result.json'); Dm=L('eval_more_D_result.json'); Um=L('scorer_untrained_more_probs.json')
    FH=L('fullhist_foldext_probs.json')
    if FH:
        fp={int(k):{int(i):x for i,x in v.items()} for k,v in FH.items()}
        fl=[(max(fp[i+off],key=fp[i+off].get) in cm[i]['valid']) if (i+off) in fp else None for i in range(len(cm))]
        okf=[i for i in ok if fl[i] is not None]
        d,p=mc([fl[i] for i in okf],[lo[i] for i in okf])
        print(f"  训练过的全历史(外部集) {pct([fl[i] for i in okf]):.1f}%   打分器 {pct([lo[i] for i in okf]):.1f}% (净{d:+d} p={p:.3f}, n={len(okf)})")
    line=f"  打分器 定位 {pct([lo[i] for i in ok]):.1f}%"
    if Bm: 
        d,p=mc([Bm[i][0] for i in ok],[lo[i] for i in ok]); line+=f"   全历史 {pct([Bm[i][0] for i in ok]):.1f}% (净{d:+d} p={p:.3f})"
    if Dm:
        d,p=mc([Dm[i][0] for i in ok],[lo[i] for i in ok]); line+=f"   索引 {pct([Dm[i][0] for i in ok]):.1f}% (净{d:+d} p={p:.3f})"
    if Um:
        up={int(k):{int(i):x for i,x in v.items()} for k,v in Um.items()}
        ul=[(max(up[i],key=up[i].get) in cm[i]['valid']) if i in up else None for i in range(len(cm))]
        line+=f"   未训练 {pct([ul[i] for i in ok if ul[i] is not None]):.1f}%"
    print(line)
    for nm,f in (('单屏读','scorer_trained_more_e2e.json'),('带历史读','scorer_trained_more_hist_e2e.json')):
        R=L(f)
        if R: 
            e=[o['e2e'] for o in R]; s2=f"  端到端 {nm}: {pct([e[i] for i in ok]):.1f}%"
            if Bm: d,p=mc([Bm[i][1] for i in ok],[e[i] for i in ok]); s2+=f"   全历史 {pct([Bm[i][1] for i in ok]):.1f}% (净{d:+d} p={p:.3f})"
            print(s2)
    for lo_,hi in [(12,15),(16,19),(20,24),(25,99)]:
        idx=[i for i in ok if lo_<=cm[i]['t']<=hi]
        if idx: print(f"    t {lo_}-{hi if hi<99 else '+'}: n={len(idx)} 打分器 {pct([lo[i] for i in idx]):.0f}%"+(f" 全历史 {pct([Bm[i][0] for i in idx]):.0f}%" if Bm else ""))
