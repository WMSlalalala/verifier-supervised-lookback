"""r0 / r1 / r2 三方对比：格式合规、区分度、可匹配性、定位分解"""
import json, re, collections, itertools, statistics, os
ROOT='/mnt/share/mwang49/guiodyssey'
FIELD=set('price prices cost name names url address phone email date time quantity size sizes color brand rating ratings review reviews stock delivery shipping coupon title id code number text label category amount total count'.split())
GENERIC=['phone screen','app screen','details page','search screen','mobile screen','screen displaying','home screen','settings screen']
def toks(s): return set(re.findall(r'[a-z0-9]+',(s or '').lower()))
def load(f):
    d={}
    p=f'{ROOT}/{f}'
    if not os.path.exists(p): return d
    for ln in open(p):
        try: x=json.loads(ln); d[x['img']]=x['entry']
        except Exception: pass
    return d
D={t:load(f'directory_{t}.jsonl') for t in ('r0','r1','r2')}
cases=json.load(open(f'{ROOT}/cases_clean.json'))
def fieldrate(E):
    return 100*sum(1 for v in E.values() if len(toks(v.split(';')[-1])&FIELD)>=1)/max(len(E),1)
def genrate(E):
    return 100*sum(1 for v in E.values() if any(g in v.lower().split(';')[0] for g in GENERIC))/max(len(E),1)
def intra(E):
    per=collections.defaultdict(list)
    for img,e in E.items(): per[img.rsplit('_',1)[0]].append(e)
    o=[]
    for es in per.values():
        for a,b in itertools.combinations(es,2):
            ta,tb=toks(a),toks(b)
            if ta|tb: o.append(len(ta&tb)/len(ta|tb))
    return o
def discrim(E):
    o=[]
    for c in cases:
        ep,t,src=c['ep'],c['t'],c['src']
        se=E.get(f'{ep}_{src}.png')
        if not se: continue
        oth=[E[f'{ep}_{i}.png'] for i in range(t) if i!=src and f'{ep}_{i}.png' in E]
        if not oth: continue
        ts=toks(se)
        o.append(max(len(ts&toks(x))/max(len(ts|toks(x)),1) for x in oth))
    return o
print(f"{'':<26}{'r0':>10}{'r1':>10}{'r2':>10}")
print('-'*56)
rows=[('条目数',       lambda E: len(E)),
      ('词数中位',     lambda E: statistics.median([len(v.split()) for v in E.values()]) if E else 0),
      ('右段含字段名%',lambda E: fieldrate(E)),
      ('左段泛称%',    lambda E: genrate(E)),
      ('同轨迹相似度', lambda E: statistics.median(intra(E)) if len(E)>1 else 0),
      ('源屏vs最像干扰',lambda E: statistics.median(discrim(E)) if E else 0)]
for nm,fn in rows:
    vals=[fn(D[t]) for t in ('r0','r1','r2')]
    fmt=lambda v: f'{v:>10.0f}' if nm in('条目数','词数中位') else (f'{v:>9.0f}%' if '%' in nm else f'{v:>10.3f}')
    print(f'{nm:<26}'+''.join(fmt(v) for v in vals))
# 定位结果
print()
res={}
for t in ('r1','r2'):
    p=f'{ROOT}/eval_{t}_result.json'
    if os.path.exists(p): res[t]=json.load(open(p))
m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json')))
keep=[i for i in range(127) if i not in bad]
r0_loc=100*sum(1 for i in keep if m['D'][i][0])/len(keep)
print(f'定位 R@1   r0={r0_loc:.1f}%', end='')
for t in ('r1','r2'):
    if t in res: print(f'  {t}={100*sum(1 for x in res[t] if x[0])/len(res[t]):.1f}%', end='')
print('   [全历史=47.5%  oracle=55.9%]')
if 'r2' in res:
    print(f"\n{'gap':<8}{'n':>5}{'r0':>7}{'r1':>7}{'r2':>7}")
    for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
        i2=[i for i,x in enumerate(res['r2']) if lo<=x[2]<=hi]
        i0=[i for i in keep if lo<=m['B'][i][2]<=hi]
        if not i2: continue
        a=100*sum(1 for i in i0 if m['D'][i][0])/len(i0)
        c=100*sum(1 for i in i2 if res['r2'][i][0])/len(i2)
        b=''
        if 'r1' in res:
            i1=[i for i,x in enumerate(res['r1']) if lo<=x[2]<=hi]
            b=f"{100*sum(1 for i in i1 if res['r1'][i][0])/len(i1):>6.0f}%"
        lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
        print(f'{lab:<8}{len(i2):>5}{a:>6.0f}%{b}{c:>6.0f}%')
