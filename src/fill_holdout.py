"""留出集结果 -> 配对检验 -> 回填论文 Table 4 的 held-out 行 + 打印 §3.20.3 用的表。固定 τ、固定指标，不调参。"""
import json,math,os,re
ROOT='/mnt/share/mwang49/guiodyssey'; P=f'{ROOT}/paper/sections/results.tex'
C=json.load(open(f'{ROOT}/cases_holdout.json')); B=json.load(open(f'{ROOT}/eval_holdout_B_result.json')); D=json.load(open(f'{ROOT}/eval_holdout_D_result.json'))
G=json.load(open(f'{ROOT}/eval_holdout_GATE_result.json')) if os.path.exists(f'{ROOT}/eval_holdout_GATE_result.json') else None
n=len(C); assert len(B)==len(D)==n
def pct(v): return 100*sum(v)/max(len(v),1)
def mc(a,b):
    x=sum(1 for p,q in zip(a,b) if p and not q); y=sum(1 for p,q in zip(a,b) if not p and q)
    if x+y==0: return 0,1.0
    chi=(abs(x-y)-1)**2/(x+y); return y-x, math.erfc(math.sqrt(chi/2))
bl,dl=[x[0] for x in B],[x[0] for x in D]; be,de=[x[1] for x in B],[x[1] for x in D]
d1,p1=mc(dl,bl); d2,p2=mc(de,be)
print(f'留出集 n={n}  t 中位 {sorted(c["t"] for c in C)[n//2]}  gap 中位 {sorted(c["gap"] for c in C)[n//2]}')
print(f'  定位  B {pct(bl):.1f}  D {pct(dl):.1f}  B净{d1:+d} p={p1:.3f}')
print(f'  端到端 B {pct(be):.1f}  D {pct(de):.1f}  B净{d2:+d} p={p2:.3f}')
if G:
    gl=[x[0] for x in G]; d3,p3=mc(gl,bl); print(f'  门控  定位 {pct(gl):.1f} (B净{d3:+d} p={p3:.3f})  端到端 {pct([x[1] for x in G]):.1f}')
for lo,hi in [(1,2),(3,7),(8,12),(13,99)]:
    i=[k for k in range(n) if lo<=C[k]['gap']<=hi]
    if i: print(f"  gap {lo}-{hi if hi<99 else '+'}: n={len(i)} B {pct([bl[k] for k in i]):.0f}% D {pct([dl[k] for k in i]):.0f}%")
row=f"14B & held-out ($t\\ge16$) & {n} & {'\\textbf{'+f'{pct(bl):.1f}'+'}' if pct(bl)>pct(dl) else f'{pct(bl):.1f}'} & {pct(dl):.1f} & {p1:.3f} & {pct(be):.1f} & {pct(de):.1f} \\\\"
s=open(P).read()
s=re.sub(r"14B & held-out & \\todo\{n\}.*?\\\\", row.replace('\\','\\\\'), s, count=1)
s=s.replace("\\todo{Held-out set: fill from eval\\_holdout results.}",
  f"The held-out set, mined with the final filter and evaluated once with every setting fixed, {'reproduces' if d1>0 else 'does not reproduce'} the ordering: {pct(bl):.1f}\\% vs.\\ {pct(dl):.1f}\\% localization (\\pval{{{p1:.3f}}}, $n={n}$) and {pct(be):.1f}\\% vs.\\ {pct(de):.1f}\\% end-to-end (\\pval{{{p2:.3f}}}).")
open(P,'w').write(s); print('-> Table 4 held-out 行已回填' if '\\todo{n}' not in s else '!! 未找到 todo 行')
