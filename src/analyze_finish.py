"""收尾汇总：端到端(14B) / 第二reader(7B) / 留出集(固定τ) 三张表 + 配对检验。缺哪个文件就跳过哪部分。"""
import json,math,os
ROOT='/mnt/share/mwang49/guiodyssey'
def L(p):
    p=f'{ROOT}/{p}'; return json.load(open(p)) if os.path.exists(p) else None
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
def pct(v): return 100*sum(v)/max(len(v),1)
def sig(p): return ' 显著' if p<0.05 else ''
CLEAN={'long':L('clean_idx_long.json'),'short':L('clean_idx_short.json')}
def sub(r,idx): return [r[i] for i in idx] if r else None
def table(title,cases,B,D,G,dn='D',which=None):
    if which in CLEAN and CLEAN[which] is not None:
        idx=CLEAN[which]; cases=[cases[i] for i in idx]; B,D,G=sub(B,idx),sub(D,idx),sub(G,idx); title+='（干净子集）'
    print('='*72); print(title+f'  n={len(cases)}')
    print(f"{'方法':<14}{'定位':>8}{'端到端':>8}")
    for nm,r in (('B 全历史',B),(f'{dn} 索引',D),('diff 门控',G)):
        if r: print(f"{nm:<14}{pct([x[0] for x in r]):>7.1f}%{pct([x[1] for x in r]):>7.1f}%")
    if G:
        for nm,r in (('B',B),(dn,D)):
            if not r: continue
            d1,p1=mc([x[0] for x in r],[x[0] for x in G]); d2,p2=mc([x[1] for x in r],[x[1] for x in G])
            print(f"  门控 vs {nm}: 定位 净{d1:+d} p={p1:.4f}{sig(p1)}   端到端 净{d2:+d} p={p2:.4f}{sig(p2)}")
        near=[i for i in range(len(cases)) if cases[i]['gap']<=2]
        if near and B: print(f"  gap1-2 (n={len(near)}): B {pct([B[i][0] for i in near]):.0f}%  {dn} {pct([D[i][0] for i in near]):.0f}%  门控 {pct([G[i][0] for i in near]):.0f}%   端到端 B {pct([B[i][1] for i in near]):.0f}% 门控 {pct([G[i][1] for i in near]):.0f}%")
# ---- 1) 端到端 14B ----
CL=L('cases_long.json'); CS=L('cases_clean.json')
table('① 长轨迹 14B（含端到端）',CL,L('eval_long_B_result.json'),L('eval_long_D_result.json'),L('eval_long_GATE_result.json'),which='long')
if L('eval_short_GATE_result.json'):
    V=[set(v) for v in L('valid_screens.json')]; m=L('full_matrix_result.json'); bad=set(L('bad_idx.json')); keep=[i for i in range(127) if i not in bad]
    BS=[(m['B'][i][4] in V[k], m['B'][i][1]) for k,i in enumerate(keep)]; ES=[(m['E'][i][4] in V[k], m['E'][i][1]) for k,i in enumerate(keep)]
    table('② 短轨迹 14B（含端到端）',CS,BS,ES,L('eval_short_GATE_result.json'),dn='E',which='short')
    pass  # 切换规则已撤回（§3.21）；干净合并趋势见 §3.21.2
# ---- 2) 第二 reader 7B ----
if L('eval_long_B_7B_result.json'):
    table('④ 长轨迹 第二 reader Qwen2.5-7B',CL,L('eval_long_B_7B_result.json'),L('eval_long_D_7B_result.json'),L('eval_long_GATE_7B_result.json'),which='long')
# ---- 3) 留出集 ----
CH=L('cases_holdout.json')
if CH and L('eval_holdout_B_result.json'):
    table('⑤ 留出集 14B（τ=0.1、切点 16 固定，未调参）',CH,L('eval_holdout_B_result.json'),L('eval_holdout_D_result.json'),L('eval_holdout_GATE_result.json'))
