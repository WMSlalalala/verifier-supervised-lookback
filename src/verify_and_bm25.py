"""Stage 0 验证 + Stage 1 BM25 对照（GUI-Odyssey 抽样 300 条）

验证：规则A 的 6.21% 上界里，有多少真的能在更早帧的 OCR 文本中找到
对照：给定第 t 步的处境，能否定位到源屏 i
  BM25-ctx    查询 = task + 当前屏文本           （现实设定：reader 不知道要搜什么）
  BM25-oracle 查询 = 答案字符串本身               （上界：reader 完美知道要搜什么）
  差值 = 查询构造的瓶颈 ← 这正是 Layer 2 目录要解决的
"""
import json, re, math, collections, os

ROOT='/mnt/share/mwang49/guiodyssey'
def norm(s):
    s=(s or '').lower().strip(); return re.sub(r'[\s,，]','',s)
def toks(s):
    return re.findall(r'[a-z0-9]+', (s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    try: d=json.loads(ln); OCR[d['img']]=d['elems']
    except Exception: pass
print(f'OCR frames: {len(OCR)}')

sample=json.load(open(f'{ROOT}/sample300.json'))
anno={}
for s in sample:
    f=f"{ROOT}/annotations/{s['ep']}.json"
    if os.path.exists(f): anno[s['ep']]=json.load(open(f))

def frame_text(ep, st):
    e=OCR.get(f'{ep}_{st}.png')
    return ' '.join(x['t'] for x in e) if e else None

# ---------- Stage 0 验证 ----------
cases=[]       # (ep, t, i, answer, gap)
n_cand=0; n_noframe=0; n_notfound=0
for s in sample:
    ep=s['ep']; d=anno.get(ep)
    if not d: continue
    L=d.get('step_length') or len(d['steps'])
    for st, raw in s['hits']:
        n_cand+=1
        ans=norm(raw)
        src=None
        for i in range(st):
            ft=frame_text(ep,i)
            if ft is None: continue
            if ans in norm(ft): src=i; break
        if src is None:
            if all(frame_text(ep,i) is None for i in range(st)): n_noframe+=1
            else: n_notfound+=1
        else:
            cases.append((ep, st, src, raw, st-src))

print(f'\n=== Stage 0 验证（抽样 300 条轨迹）===')
print(f'  候选（规则A 上界）        {n_cand}')
print(f'  ✓ 在更早帧 OCR 中找到      {len(cases)}   ({100*len(cases)/max(n_cand,1):.1f}% of 候选)')
print(f'  ✗ 更早帧有文本但没找到     {n_notfound}')
print(f'  - 更早帧 OCR 缺失          {n_noframe}')
if cases:
    gs=sorted(c[4] for c in cases)
    print(f'  gap 中位/均值/最大        {gs[len(gs)//2]} / {sum(gs)/len(gs):.1f} / {max(gs)}')
    print(f'  gap>=5 的占比             {100*sum(1 for g in gs if g>=5)/len(gs):.1f}%')
    eps=len(set(c[0] for c in cases))
    print(f'  覆盖轨迹                  {eps}/300')
    print(f'\n  样例:')
    for c in cases[:6]:
        print(f'    gap={c[4]:<3} ep={c[0][:10]} t={c[1]} src={c[2]}  ans={c[3][:60]!r}')

if not cases:
    print('\n无可用 case，终止'); raise SystemExit

# ---------- Stage 1 BM25 ----------
class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs=[toks(d) for d in docs]; self.k1=k1; self.b=b
        self.N=len(self.docs); self.avgdl=sum(len(d) for d in self.docs)/max(self.N,1)
        self.df=collections.Counter()
        for d in self.docs: self.df.update(set(d))
        self.tf=[collections.Counter(d) for d in self.docs]
    def score(self, q):
        q=toks(q); out=[]
        for i,d in enumerate(self.docs):
            s=0.0; dl=len(d)
            for w in q:
                if w not in self.tf[i]: continue
                idf=math.log(1+(self.N-self.df[w]+0.5)/(self.df[w]+0.5))
                f=self.tf[i][w]
                s+=idf*f*(self.k1+1)/(f+self.k1*(1-self.b+self.b*dl/max(self.avgdl,1)))
            out.append(s)
        return out

def evaluate(mode):
    r1=r3=r5=tot=0; ranks=[]
    for ep, t, src, raw, gap in cases:
        d=anno[ep]; task=d['task_info'].get('task','')
        texts=[]; ids=[]
        for i in range(t):                      # 严格时间边界 i < t
            ft=frame_text(ep,i)
            if ft is None: continue
            texts.append(ft); ids.append(i)
        if src not in ids or len(ids)<2: continue
        bm=BM25(texts)
        if mode=='ctx':
            cur=frame_text(ep,t) or ''
            q=task+' '+cur
        else:                                    # oracle：完美查询
            q=raw
        sc=bm.score(q)
        order=[ids[j] for j in sorted(range(len(sc)), key=lambda j:-sc[j])]
        rk=order.index(src)+1; ranks.append(rk); tot+=1
        r1+= rk<=1; r3+= rk<=3; r5+= rk<=5
    if not tot: return None
    rs=sorted(ranks)
    return dict(n=tot, R1=100*r1/tot, R3=100*r3/tot, R5=100*r5/tot,
                medrank=rs[len(rs)//2], avgcand=sum(1 for _ in ranks))

print(f'\n=== Stage 1 BM25 源屏定位（严格 i<t）===')
for mode,label in [('ctx','BM25-ctx    查询=task+当前屏（现实）'),
                   ('oracle','BM25-oracle 查询=答案串（上界）')]:
    r=evaluate(mode)
    if r: print(f'  {label}\n      n={r["n"]}  R@1={r["R1"]:.1f}  R@3={r["R3"]:.1f}  R@5={r["R5"]:.1f}  中位排名={r["medrank"]}')

json.dump([{'ep':c[0],'t':c[1],'src':c[2],'ans':c[3],'gap':c[4]} for c in cases],
          open(f'{ROOT}/cases.json','w'), ensure_ascii=False, indent=1)
print(f'\n已写出 {len(cases)} 个 case -> cases.json')
