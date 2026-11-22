"""指标修正：定位正确 = pred 落在任一含答案的屏，而非恒等于最早出现的 src"""
import json,re
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())
ROOT='/mnt/share/mwang49/guiodyssey'
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/cases_clean.json'))
VALID=[]
for c in cases:
    ep,t,na=c['ep'],c['t'],norm(c['ans'])
    VALID.append(sorted(j for j in range(t) if na and na in norm(OCR.get(f'{ep}_{j}.png',''))))
json.dump(VALID, open(f'{ROOT}/valid_screens.json','w'))
n_amb=sum(1 for v in VALID if len(v)>1)
print(f'valid_screens.json 已存  歧义 case {n_amb}/{len(VALID)} ({100*n_amb/len(VALID):.0f}%)')
