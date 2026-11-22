"""[长轨迹] 为 cases_long 的帧补生成 r0 目录条目(追加到 directory_r0.jsonl)。: prompt-only writer (Qwen2.5-7B-Instruct)
对每帧 OCR 文本生成一行 <=32 token 的目录条目。对应 plan §1.3 组 D（ReadAgent 基线）。"""
import json, os, torch, re
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT='/mnt/share/mwang49/guiodyssey'
MODEL='Qwen/Qwen2.5-7B-Instruct'
OUT=f'{ROOT}/directory_r0.jsonl'
os.environ.setdefault('HF_HOME','/mnt/share/mwang49/hf_cache')

cases=json.load(open(f'{ROOT}/cases_holdout.json'))
need=set()
anno={}
for c in cases:
    ep=c['ep']
    if ep not in anno:
        anno[ep]=json.load(open(f'{ROOT}/annotations/{ep}.json'))
    for i in range(c['t']):            # 只需要 i<t 的帧
        need.add(f"{ep}_{i}.png")
print(f'需要生成目录的帧: {len(need)}', flush=True)

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=d['elems']

done=set()
if os.path.exists(OUT):
    for ln in open(OUT):
        try: done.add(json.loads(ln)['img'])
        except Exception: pass
todo=[f for f in sorted(need) if f in OCR and f not in done]
print(f'todo: {len(todo)}', flush=True)

tok=AutoTokenizer.from_pretrained(MODEL, padding_side='left')
model=AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map='auto')
model.eval()

SYS=("You write one-line directory entries for a screen archive. "
     "Given the text elements of one phone screen, output ONE line, at most 20 words, "
     "naming (a) what the screen is, then a semicolon, then (b) which kinds of lookupable "
     "values it contains (e.g. price, address, url, name, date). "
     "Do NOT output the values themselves. No extra text.")

def prompt_for(img):
    txt=' | '.join(e['t'] for e in OCR[img][:50])
    return tok.apply_chat_template(
        [{"role":"system","content":SYS},
         {"role":"user","content":f"Screen elements:\n{txt}\n\nDirectory entry:"}],
        tokenize=False, add_generation_prompt=True)

out=open(OUT,'a'); B=8
for i in range(0,len(todo),B):
    batch=todo[i:i+B]
    enc=tok([prompt_for(f) for f in batch], return_tensors='pt',
            padding=True, truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        g=model.generate(**enc, max_new_tokens=40, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    for f,seq in zip(batch, g):
        txt=tok.decode(seq[enc['input_ids'].shape[1]:], skip_special_tokens=True)
        txt=re.sub(r'\s+',' ',txt).strip().split('\n')[0][:200]
        out.write(json.dumps({'img':f,'entry':txt})+'\n')
    if (i//B)%20==0:
        out.flush(); print(f'[gen] {i+len(batch)}/{len(todo)}', flush=True)
out.close(); print('GEN_DONE', flush=True)
