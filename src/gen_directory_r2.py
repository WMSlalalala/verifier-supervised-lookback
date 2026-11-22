"""r2 目录：prompt-only writer，强制 <具体内容>; <字段名> 双段格式。
检验 §3.8.5 假设——好条目须同时具备内容特征(区分度)与字段名(可匹配性)。
不含训练，是纯 prompt 消融，用于决定是否值得重训 writer。"""
import json, os, torch, re
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT='/mnt/share/mwang49/guiodyssey'
MODEL='Qwen/Qwen2.5-7B-Instruct'
OUT=f'{ROOT}/directory_r2.jsonl'
os.environ.setdefault('HF_HOME','/mnt/share/mwang49/hf_cache')

SYS=("You write one-line directory entries for a phone-screen archive. "
     "A later agent reads these entries to decide WHICH screen to re-open when it needs a specific value.\n"
     "Output EXACTLY one line, in this format:\n"
     "  <specific subject of THIS screen>; <kinds of values it holds>\n"
     "LEFT of the semicolon: the concrete subject - product names, brands, categories, or the specific "
     "task this screen serves. It must tell this screen apart from other screens of the same app. "
     "NEVER write generic labels such as 'Phone screen', 'App screen', 'Details page', 'Search screen'.\n"
     "RIGHT of the semicolon: a comma-separated list of the KINDS of lookupable values present, chosen from "
     "words like price, address, url, name, date, time, size, brand, rating, review count, quantity, stock, "
     "phone, email, category, delivery, coupon.\n"
     "Never output the values themselves. At most 20 words total. English only. No extra text.")

# few-shot：两边都示范到位
FEW=[("Cheez-It | Pringles | Variety Pack | 40 Count | $18.99 | 4.5 stars | 2,341 reviews | Add to Cart | Free delivery",
      "Cheez-It & Pringles snack variety packs; price, count, brand, rating, review count, delivery"),
     ("Google | Search | Photos | Lens | Translate | Shopping | Scan barcode | Search with your camera",
      "Google Lens camera search, barcode & translate; name, url, category"),
     ("Marriott Downtown | 123 Main St | Check-in Fri Mar 8 | 2 nights | $214/night | Free cancellation | Map",
      "Marriott Downtown hotel booking; address, price, date, name, cancellation policy")]

cases=json.load(open(f'{ROOT}/cases_clean.json'))
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=d['elems']
need=set()
for c in cases:
    for i in range(c['t']+1): need.add(f"{c['ep']}_{i}.png")
need={x for x in need if x in OCR}
done=set()
if os.path.exists(OUT):
    for ln in open(OUT):
        try: done.add(json.loads(ln)['img'])
        except Exception: pass
todo=sorted(need-done); print(f'需生成 {len(todo)} 帧 (已有 {len(done)})', flush=True)

tok=AutoTokenizer.from_pretrained(MODEL, padding_side='left')
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()

def prompt_for(img):
    txt=' | '.join(e['t'] for e in OCR[img][:50])
    msgs=[{"role":"system","content":SYS}]
    for u,a in FEW:
        msgs.append({"role":"user","content":f"Screen elements:\n{u}\n\nDirectory entry:"})
        msgs.append({"role":"assistant","content":a})
    msgs.append({"role":"user","content":f"Screen elements:\n{txt}\n\nDirectory entry:"})
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

out=open(OUT,'a'); B=8
for i in range(0,len(todo),B):
    batch=todo[i:i+B]
    enc=tok([prompt_for(f) for f in batch], return_tensors='pt',
            padding=True, truncation=True, max_length=2048).to(model.device)
    with torch.no_grad():
        g=model.generate(**enc, max_new_tokens=48, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    for f,seq in zip(batch, g):
        txt=tok.decode(seq[enc['input_ids'].shape[1]:], skip_special_tokens=True)
        txt=re.sub(r'\s+',' ',txt).strip().split('\n')[0][:200]
        out.write(json.dumps({'img':f,'entry':txt})+'\n')
    if (i//B)%20==0:
        out.flush(); print(f'[gen] {i+len(batch)}/{len(todo)}', flush=True)
out.close(); print('GEN_DONE', flush=True)
