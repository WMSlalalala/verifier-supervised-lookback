"""Stage 1 完整对照：源屏定位
语料固定为 i<t 的帧，变的只有 (索引表示, 查询)。

组  索引表示                查询              含义
A   verbatim OCR 全文       task+当前屏       现实下界
B   启发式摘要(前8元素)     task+当前屏       固定索引
D   LLM 目录条目(round-0)   task+当前屏       prompt-only writer
F   verbatim OCR 全文       答案串            上界(完美查询)
"""
import json, re, math, collections, os
ROOT='/mnt/share/mwang49/guiodyssey'

def norm(s): return re.sub(r'[\s,，]','',(s or '').lower().strip())
def toks(s): return re.findall(r'[a-z0-9]+',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    try: d=json.loads(ln); OCR[d['img']]=d['elems']
    except Exception: pass

DIR={}
if os.path.exists(f'{ROOT}/directory_r0.jsonl'):
    for ln in open(f'{ROOT}/directory_r0.jsonl'):
        try: d=json.loads(ln); DIR[d['img']]=d['entry']
        except Exception: pass

cases=json.load(open(f'{ROOT}/cases.json'))
anno={}
for c in cases:
    if c['ep'] not in anno:
        anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))
print(f'OCR {len(OCR)} frames | directory {len(DIR)} entries | cases {len(cases)}')

def verbatim(ep,i):
    e=OCR.get(f'{ep}_{i}.png');  return ' '.join(x['t'] for x in e) if e else None
def heuristic(ep,i):
    e=OCR.get(f'{ep}_{i}.png')
    if e is None: return None
    apps=' '.join(anno[ep]['task_info'].get('app') or [])
    top=sorted(e,key=lambda x:(x['b'][1],x['b'][0]))[:8]
    return apps+' '+' '.join(x['t'] for x in top)
def llmdir(ep,i):
    k=f'{ep}_{i}.png'
    return DIR.get(k) if k in DIR else (None if k not in OCR else '')

class BM25:
    def __init__(self,docs,k1=1.5,b=0.75):
        self.d=[toks(x) for x in docs]; self.k1=k1; self.b=b
        self.N=len(self.d); self.avg=sum(len(x) for x in self.d)/max(self.N,1)
        self.df=collections.Counter()
        for x in self.d: self.df.update(set(x))
        self.tf=[collections.Counter(x) for x in self.d]
    def rank(self,q):
        q=toks(q); sc=[]
        for i,x in enumerate(self.d):
            s=0.0; dl=len(x)
            for w in q:
                f=self.tf[i].get(w,0)
                if not f: continue
                idf=math.log(1+(self.N-self.df[w]+0.5)/(self.df[w]+0.5))
                s+=idf*f*(self.k1+1)/(f+self.k1*(1-self.b+self.b*dl/max(self.avg,1)))
            sc.append(s)
        return sc

def run(repr_fn, query_mode, bucket=None):
    r1=r3=r5=tot=0; ranks=[]; toklen=[]
    for c in cases:
        ep,t,src,ans,gap=c['ep'],c['t'],c['src'],c['ans'],c['gap']
        if bucket and not (bucket[0]<=gap<=bucket[1]): continue
        docs=[]; ids=[]
        for i in range(t):
            r=repr_fn(ep,i)
            if r is None: continue
            docs.append(r); ids.append(i)
        if src not in ids or len(ids)<2: continue
        q = ans if query_mode=='oracle' else \
            (anno[ep]['task_info'].get('task','')+' '+(verbatim(ep,t) or ''))
        sc=BM25(docs).rank(q)
        order=[ids[j] for j in sorted(range(len(sc)),key=lambda j:-sc[j])]
        rk=order.index(src)+1; ranks.append(rk); tot+=1
        r1+=rk<=1; r3+=rk<=3; r5+=rk<=5
        toklen.append(sum(len(toks(d)) for d in docs))
    if not tot: return None
    rs=sorted(ranks)
    return dict(n=tot,R1=100*r1/tot,R3=100*r3/tot,R5=100*r5/tot,
                med=rs[len(rs)//2], tok=sum(toklen)/len(toklen))

GROUPS=[('A  verbatim / ctx-query    ', verbatim,  'ctx'),
        ('B  启发式摘要 / ctx-query  ', heuristic, 'ctx'),
        ('D  LLM目录(r0) / ctx-query ', llmdir,    'ctx'),
        ('F  verbatim / oracle-query ', verbatim,  'oracle')]

print(f'\n{"="*74}\nStage 1  源屏定位（严格 i<t）')
print(f'{"组":<28}{"n":>5}{"R@1":>7}{"R@3":>7}{"R@5":>7}{"中位":>6}{"索引token":>11}')
for name,fn,qm in GROUPS:
    if fn is llmdir and not DIR: print(f'{name}  (未生成目录，跳过)'); continue
    r=run(fn,qm)
    if r: print(f'{name}{r["n"]:>5}{r["R1"]:>7.1f}{r["R3"]:>7.1f}{r["R5"]:>7.1f}{r["med"]:>6}{r["tok"]:>11.0f}')

print(f'\n{"="*74}\n按 gap 分层（组 A / 组 F）')
print(f'{"gap":<12}{"n":>5}{"A R@1":>9}{"F R@1":>9}{"差值":>9}')
for lo,hi,lab in [(1,2,'1-2'),(3,5,'3-5'),(6,10,'6-10'),(11,99,'>=11')]:
    a=run(verbatim,'ctx',(lo,hi)); f=run(verbatim,'oracle',(lo,hi))
    if a and f:
        print(f'{lab:<12}{a["n"]:>5}{a["R1"]:>9.1f}{f["R1"]:>9.1f}{f["R1"]-a["R1"]:>9.1f}')
