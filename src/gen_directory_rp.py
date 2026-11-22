"""可实现版 oracle：用 oracle_directory.py 的检索 prompt(CAND_P) + T=0.9 采样，为短集全部帧各写一行 -> directory_rp.jsonl"""
import json,torch,re
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'; MODEL='Qwen/Qwen2.5-7B-Instruct'
CAND_P=("Below is the text extracted from one Android screen.\n\n{txt}\n\n"
        "Write ONE short directory line (max 20 words) that will later help someone "
        "DECIDE WHETHER TO RE-OPEN THIS SCREEN when they need a specific value. "
        "Name the screen type and WHICH KINDS OF VALUES it contains — do not list the values themselves.\n"
        "Output ONLY the line.")
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
C=json.load(open(f'{ROOT}/cases_clean.json')); I=json.load(open(f'{ROOT}/clean_idx_short.json'))
frames=sorted(set(f"{C[k]['ep']}_{i}.png" for k in I for i in range(C[k]['t'])))
tok=AutoTokenizer.from_pretrained(MODEL,padding_side='left'); model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='cuda'); model.eval()
torch.manual_seed(0); out=open(f'{ROOT}/directory_rp.jsonl','w'); B=16
for s in range(0,len(frames),B):
    batch=frames[s:s+B]
    ps=[tok.apply_chat_template([{"role":"user","content":CAND_P.format(txt=OCR.get(f,'')[:2500])}],tokenize=False,add_generation_prompt=True) for f in batch]
    enc=tok(ps,return_tensors='pt',padding=True).to('cuda')
    with torch.no_grad(): o=model.generate(**enc,max_new_tokens=40,do_sample=True,temperature=0.9,top_p=0.95,pad_token_id=tok.eos_token_id)
    for f,seq in zip(batch,o):
        line=tok.decode(seq[enc['input_ids'].shape[1]:],skip_special_tokens=True).strip().split('\n')[0][:160]
        out.write(json.dumps({'img':f,'entry':line})+'\n')
    if (s//B)%10==0: print(f'{s+len(batch)}/{len(frames)}',flush=True)
out.close(); print('GEN_DONE',len(frames))
