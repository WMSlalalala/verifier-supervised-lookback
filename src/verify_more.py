"""长轨迹 case 验证：答案串在更早帧 OCR 中出现 -> case；同时输出修正指标所需的 valid_screens_more.json"""
import json, re, os, statistics
ROOT='/mnt/share/mwang49/guiodyssey'
def norm(s): s=(s or '').lower().strip(); return re.sub(r'[\s,，]','',s)
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    try: d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'])
    except Exception: pass
sample=json.load(open(f'{ROOT}/sample_more.json'))
INS={}
for s_ in sample:
    f_=f"{ROOT}/annotations/{s_['ep']}.json"
    if os.path.exists(f_): INS[s_['ep']]=norm(json.load(open(f_))['task_info'].get('instruction',''))
cases=[]; valid=[]; n_cand=0; n_nf=0
for s in sample:
    ep=s['ep']
    for st,raw in s['hits']:
        n_cand+=1; ans=norm(raw)
        if not OCR.get(f'{ep}_{st}.png'): continue          # 当前屏须有 OCR
        if ans in norm(OCR[f'{ep}_{st}.png']): n_oncur=globals().get('n_oncur',0)+1; globals()['n_oncur']=n_oncur; continue   # 排除：答案已在当前屏（非延迟需求）
        if ans in INS.get(ep,''): n_ins=globals().get('n_ins',0)+1; globals()['n_ins']=n_ins; continue   # 排除：答案在 instruction 字段
        hits=[i for i in range(st) if OCR.get(f'{ep}_{i}.png') and ans in norm(OCR[f'{ep}_{i}.png'])]
        if not hits: n_nf+=1; continue
        src=hits[0]
        cases.append({'ep':ep,'t':st,'src':src,'ans':raw,'gap':st-src})
        valid.append(hits)
print(f'候选 {n_cand}  -> case {len(cases)}  (未找到 {n_nf}, 答案在当前屏被排除 {globals().get("n_oncur",0)}, instruction 泄漏排除 {globals().get("n_ins",0)})')
if cases:
    t=[c['t'] for c in cases]; g=[c['gap'] for c in cases]
    print(f't 中位 {statistics.median(t)} 最大 {max(t)}   gap 中位 {statistics.median(g)} 最大 {max(g)}')
    for lo,hi in [(16,19),(20,24),(25,29),(30,99)]:
        print(f'  t {lo}-{hi}: {sum(1 for x in t if lo<=x<=hi)}')
    print(f'歧义(>=2屏含答案): {sum(1 for v in valid if len(v)>1)}/{len(cases)}')
json.dump(cases, open(f'{ROOT}/cases_more.json','w'), ensure_ascii=False, indent=1)
json.dump(valid, open(f'{ROOT}/valid_screens_more.json','w'))
print('-> cases_more.json, valid_screens_more.json')
