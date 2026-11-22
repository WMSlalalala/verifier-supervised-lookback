"""用训练后的 writer (LoRA) 重建目录 -> directory_r1.jsonl"""
import json, os, torch, time
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-7B-Instruct')
OUT=f'{ROOT}/directory_r1.jsonl'
PROMPT=("Below is the text extracted from one Android screen.\n\n{txt}\n\n"
        "Write ONE short directory line (max 20 words) that will later help someone "
        "DECIDE WHETHER TO RE-OPEN THIS SCREEN when they need a specific value. "
        "Name the screen type and WHICH KINDS OF VALUES it contains — do not list the values themselves.\n"
        "Output ONLY the line.")
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/cases_clean.json'))
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

tok=AutoTokenizer.from_pretrained(MODEL)
base=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto')
model=PeftModel.from_pretrained(base, f'{ROOT}/writer_lora'); model.eval()
dev=next(model.parameters()).device
t0=time.time(); f=open(OUT,'a')
for k,img in enumerate(todo):
    ids=tok.apply_chat_template([{"role":"user","content":PROMPT.format(txt=OCR[img][:2500])}],
                                add_generation_prompt=True, return_tensors='pt').to(dev)
    with torch.no_grad():
        o=model.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=40,
                         do_sample=False, pad_token_id=tok.eos_token_id)
    e=tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip().split('\n')[0][:160]
    f.write(json.dumps({'img':img,'entry':e}, ensure_ascii=False)+'\n'); f.flush()
    if (k+1)%200==0: print(f'  [gen] {k+1}/{len(todo)}  {time.time()-t0:.0f}s', flush=True)
print(f'GEN_DONE -> {OUT}')
