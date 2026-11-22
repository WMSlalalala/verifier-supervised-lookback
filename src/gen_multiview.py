"""多视角目录：每屏用采样生成 K 个互异条目。
对照设计——同模型(7B)、同 prompt、同采样方式，唯一变量是评估时呈现几个视角。
用于检验 §3.14.3：oracle 的优势是否可通过「把多个视角都给 reader」兑现。"""
import json, os, torch, re
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-7B-Instruct')
K=int(os.environ.get('K','3'))
OUT=f'{ROOT}/directory_mv{K}.jsonl'
os.environ.setdefault('HF_HOME','/mnt/share/mwang49/hf_cache')

# 与 oracle 候选生成一致的 prompt（该 prompt 下的候选被验证可达 56%）
CAND_P=("Below is the text extracted from one Android screen.\n\n{txt}\n\n"
        "Write ONE short directory line (max 20 words) that will later help someone "
        "DECIDE WHETHER TO RE-OPEN THIS SCREEN when they need a specific value. "
        "Name the screen type and WHICH KINDS OF VALUES it contains - do not list the values themselves.\n"
        "Output ONLY the line.")

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
todo=sorted(need-done); print(f'需生成 {len(todo)} 帧 x K={K} (已有 {len(done)})', flush=True)

tok=AutoTokenizer.from_pretrained(MODEL, padding_side='left')
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()

def prompt_for(img):
    txt=' | '.join(e['t'] for e in OCR[img][:50])
    return tok.apply_chat_template([{"role":"user","content":CAND_P.format(txt=txt)}],
                                   tokenize=False, add_generation_prompt=True)

out=open(OUT,'a'); B=4
for i in range(0,len(todo),B):
    batch=todo[i:i+B]
    enc=tok([prompt_for(f) for f in batch], return_tensors='pt',
            padding=True, truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        g=model.generate(**enc, max_new_tokens=44, do_sample=True, temperature=0.9, top_p=0.95,
                         num_return_sequences=K, pad_token_id=tok.pad_token_id or tok.eos_token_id)
    L=enc['input_ids'].shape[1]
    for bi,f in enumerate(batch):
        ents=[]
        for kk in range(K):
            seq=g[bi*K+kk]
            t=tok.decode(seq[L:], skip_special_tokens=True)
            t=re.sub(r'\s+',' ',t).strip().split('\n')[0][:160]
            if t: ents.append(t)
        out.write(json.dumps({'img':f,'entries':ents}, ensure_ascii=False)+'\n')
    if (i//B)%40==0:
        out.flush(); print(f'[gen] {i+len(batch)}/{len(todo)}', flush=True)
out.close(); print('GEN_DONE', flush=True)
