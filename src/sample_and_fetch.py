import json, glob, re, random, os, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

ROOT='/mnt/share/mwang49/guiodyssey'
random.seed(0)
def norm(s):
    s=(s or '').lower().strip(); return re.sub(r'[\s,，]','',s)

# 1. 找出有候选的轨迹
cand_eps=[]
for f in glob.glob(f'{ROOT}/annotations/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    task=norm(d.get('task_info',{}).get('task'))
    hits=[]
    for s in d.get('steps',[]):
        if s.get('action','').upper()=='TEXT':
            raw = s.get('info') if isinstance(s.get('info'),str) else s.get('ps')
            t=norm(raw)
            if len(t)>=3 and t not in task:
                hits.append((s.get('step'), raw))
    if hits: cand_eps.append((d['episode_id'], d.get('step_length') or len(d['steps']), hits))

print(f'有候选的轨迹: {len(cand_eps)}')
sample = random.sample(cand_eps, 300)
json.dump([{'ep':e,'len':l,'hits':h} for e,l,h in sample], open(f'{ROOT}/sample300.json','w'))

# 2. 需要的截图 = 抽样轨迹的全部帧
index = json.load(open(f'{ROOT}/screenshot_index.json'))
need=[]
for ep,L,hits in sample:
    for st in range(L):
        fn=f'{ep}_{st}.png'
        if fn in index: need.append((fn, index[fn]))
print(f'需要下载: {len(need)} 张')
json.dump(need, open(f'{ROOT}/need_files.json','w'))

# 3. 并行下载
OUT=f'{ROOT}/shots'; os.makedirs(OUT, exist_ok=True)
BASE='https://huggingface.co/datasets/OpenGVLab/GUI-Odyssey/resolve/main/'
done=[0]; fail=[0]
def get(item):
    fn,d = item
    dst=os.path.join(OUT,fn)
    if os.path.exists(dst) and os.path.getsize(dst)>1000:
        done[0]+=1; return
    for _ in range(3):
        try:
            urllib.request.urlretrieve(BASE+d+'/'+fn, dst); done[0]+=1
            if done[0]%400==0: print(f'  {done[0]}/{len(need)}', flush=True)
            return
        except Exception: time.sleep(1)
    fail[0]+=1

with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(get, need))
print(f'DONE downloaded={done[0]} failed={fail[0]}')
