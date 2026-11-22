"""[留出集] 长轨迹采样（排除 sample300 与 sample_long，seed=7）：从 len>=MINLEN 且含 t>=MINT 候选步的轨迹中抽 N 条（排除 sample300），下载全部帧。
目的：检验 §3.17.4 —— 长上下文下全历史退化而索引不退化。"""
import json, glob, re, random, os, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
ROOT='/mnt/share/mwang49/guiodyssey'
MINLEN=int(os.environ.get('MINLEN','20')); MINT=int(os.environ.get('MINT','16')); N=int(os.environ.get('N','300'))
random.seed(11)
def norm(s): s=(s or '').lower().strip(); return re.sub(r'[\s,，]','',s)
old=set(x['ep'] for x in json.load(open(f'{ROOT}/sample300.json')))|set(x['ep'] for x in json.load(open(f'{ROOT}/sample_long.json')))|set(x['ep'] for x in json.load(open(f'{ROOT}/sample_holdout.json')))
cand=[]
for f in glob.glob(f'{ROOT}/annotations/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    ep=d['episode_id']
    if ep in old: continue
    L=d.get('step_length') or len(d['steps'])
    if L<MINLEN: continue
    task=norm(d.get('task_info',{}).get('task'))
    hits=[]
    for s in d.get('steps',[]):
        if s.get('action','').upper()=='TEXT':
            raw=s.get('info') if isinstance(s.get('info'),str) else s.get('ps')
            t=norm(raw)
            if len(t)>=3 and t not in task and s.get('step',0)>=MINT: hits.append((s.get('step'),raw))
    if hits: cand.append((ep,L,hits))
print(f'len>={MINLEN} 且含 t>={MINT} 候选的轨迹（排除旧样本）: {len(cand)}', flush=True)
sample=random.sample(cand, min(N,len(cand)))
json.dump([{'ep':e,'len':l,'hits':h} for e,l,h in sample], open(f'{ROOT}/sample_more.json','w'))
index=json.load(open(f'{ROOT}/screenshot_index.json'))
need=[]
for ep,L,hits in sample:
    mx=max(st for st,_ in hits)          # 只需 0..max(hit step) 的帧
    for st in range(mx+1):
        fn=f'{ep}_{st}.png'
        if fn in index: need.append((fn,index[fn]))
print(f'抽样 {len(sample)} 轨迹，需下载 {len(need)} 张', flush=True)
json.dump(need, open(f'{ROOT}/need_more.json','w'))
OUT=f'{ROOT}/shots'; os.makedirs(OUT,exist_ok=True)
BASE='https://huggingface.co/datasets/OpenGVLab/GUI-Odyssey/resolve/main/'
done=[0]; fail=[0]
def get(item):
    fn,d=item; dst=os.path.join(OUT,fn)
    if os.path.exists(dst) and os.path.getsize(dst)>1000: done[0]+=1; return
    for _ in range(3):
        try:
            urllib.request.urlretrieve(BASE+d+'/'+fn,dst); done[0]+=1
            if done[0]%500==0: print(f'  [dl] {done[0]}/{len(need)}', flush=True)
            return
        except Exception: time.sleep(1)
    fail[0]+=1
with ThreadPoolExecutor(max_workers=16) as ex: list(ex.map(get,need))
print(f'DL_DONE downloaded={done[0]} failed={fail[0]}', flush=True)
