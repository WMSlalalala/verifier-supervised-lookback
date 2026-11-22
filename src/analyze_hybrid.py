"""混合上下文 vs 全历史(B) / 索引(D或E) 配对分析，长短轨迹各一组；重点看 gap 1-2 盲区是否修复。"""
import json, math, os
ROOT='/mnt/share/mwang49/guiodyssey'
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
def pct(v): return 100*sum(v)/max(len(v),1)
def load(tag):
    p=f'{ROOT}/eval_{tag}_result.json'
    return json.load(open(p)) if os.path.exists(p) else None
for CASES in ('long','short'):
    if CASES=='long':
        cases=json.load(open(f'{ROOT}/cases_long.json')); V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens_long.json'))]
        B=load('long_B'); D=load('long_D')
        base={'B 全历史':[(x[0],x[1]) for x in B],'D 索引':[(x[0],x[1]) for x in D]}
    else:
        cases=json.load(open(f'{ROOT}/cases_clean.json')); V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
        m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json'))); keep=[i for i in range(127) if i not in bad]
        base={'B 全历史':[(m['B'][i][4] in V[k], m['B'][i][1]) for k,i in enumerate(keep)],
              'E 索引':[(m['E'][i][4] in V[k], m['E'][i][1]) for k,i in enumerate(keep)]}
    hyb={}
    for tag,nm in ((f'{CASES}_H1','H 混合K=1'),(f'{CASES}_H2','H 混合K=2'),(f'{CASES}_H3','H 混合K=3'),(f'{CASES}_H2n','H 混合K=2+提示'),(f'{CASES}_T2','T 两段式K=2')):
        r=load(tag)
        if r: hyb[nm]=[(x[0],x[1]) for x in r]
    if not hyb: print(f'[{CASES}] 尚无混合结果'); continue
    N=len(cases)
    print('='*70); print(f'[{CASES}] n={N}')
    print(f"{'方法':<16}{'定位':>8}{'端到端':>8}")
    for nm,r in list(base.items())+list(hyb.items()):
        print(f"{nm:<16}{pct([x[0] for x in r]):>7.1f}%{pct([x[1] for x in r]):>7.1f}%")
    print('\n配对检验（混合 vs 基线）')
    for hn,hr in hyb.items():
        for bn,br in base.items():
            d1,p1=mc([x[0] for x in br],[x[0] for x in hr]); d2,p2=mc([x[1] for x in br],[x[1] for x in hr])
            print(f"  {hn:<14} vs {bn:<8} 定位 净{d1:+3d} p={p1:.3f}{' 显著' if p1<0.05 else ''}   端到端 净{d2:+3d} p={p2:.3f}{' 显著' if p2<0.05 else ''}")
    print('\n按 gap（定位）')
    cols=list(base.keys())+list(hyb.keys())
    print(f"{'gap':<7}{'n':>4}"+''.join(f'{c[:10]:>12}' for c in cols))
    bins=[(1,2),(3,4),(5,7),(8,12),(13,99)] if CASES=='long' else [(1,2),(3,4),(5,7),(8,99)]
    for lo,hi in bins:
        idx=[i for i in range(N) if lo<=cases[i]['gap']<=hi]
        if not idx: continue
        row=''.join(f"{pct([r[i][0] for i in idx]):>11.0f}%" for r in list(base.values())+list(hyb.values()))
        print(f"{(f'{lo}-{hi}' if hi<99 else f'{lo}+'):<7}{len(idx):>4}{row}")
    if CASES=='long':
        idx=[i for i in range(N) if cases[i]['gap']<=2]
        print(f'\ngap 1-2 子集 (n={len(idx)}) 配对：')
        for hn,hr in hyb.items():
            for bn,br in base.items():
                d,p=mc([br[i][0] for i in idx],[hr[i][0] for i in idx])
                print(f"  {hn:<14} vs {bn:<8} 净{d:+3d}  p={p:.3f}{' 显著' if p<0.05 else ''}")
    print('\n按 t（定位）')
    tb=[(16,19),(20,24),(25,29),(30,99)] if CASES=='long' else [(1,7),(8,11),(12,15),(16,99)]
    for lo,hi in tb:
        idx=[i for i in range(N) if lo<=cases[i]['t']<=hi]
        if not idx: continue
        row=''.join(f"{pct([r[i][0] for i in idx]):>11.0f}%" for r in list(base.values())+list(hyb.values()))
        print(f"{(f'{lo}-{hi}' if hi<99 else f'{lo}+'):<7}{len(idx):>4}{row}")
