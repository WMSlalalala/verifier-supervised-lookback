"""OCR GUI-Odyssey sampled screenshots -> {img, elems:[{t,b,c}]} jsonl.
复用 GUI_agent/src/vision_parse.py 的格式与 MIN_CONF。"""
import json, os, glob, sys
MIN_CONF = 0.3
OUT = '/mnt/share/mwang49/guiodyssey/parse_odyssey.jsonl'
SHOTS = '/mnt/share/mwang49/guiodyssey/shots'

done = set()
if os.path.exists(OUT):
    for ln in open(OUT):
        try: done.add(json.loads(ln)['img'])
        except Exception: pass
print(f'{len(done)} already parsed', flush=True)

files = sorted(glob.glob(f'{SHOTS}/*.png'))
todo = [f for f in files if os.path.basename(f) not in done]
print(f'{len(files)} total, {len(todo)} todo', flush=True)

import easyocr
reader = easyocr.Reader(['en'], gpu=True, verbose=False)
out = open(OUT, 'a')
for n, f in enumerate(todo, 1):
    try: res = reader.readtext(f)
    except Exception as e:
        print(f'[warn] {f}: {e!r}', flush=True); res = []
    elems = []
    for bb, txt, conf in res:
        if conf < MIN_CONF or not str(txt).strip(): continue
        xs=[p[0] for p in bb]; ys=[p[1] for p in bb]
        elems.append({'t': str(txt)[:80],
                      'b': [int(min(xs)),int(min(ys)),int(max(xs)),int(max(ys))],
                      'c': round(float(conf),3)})
    out.write(json.dumps({'img': os.path.basename(f), 'elems': elems})+'\n')
    if n % 200 == 0:
        out.flush(); print(f'[ocr] {n}/{len(todo)}', flush=True)
out.close()
print(f'OCR_DONE {len(todo)}', flush=True)
