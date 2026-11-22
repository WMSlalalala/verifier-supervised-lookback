"""同一 prompt、同一 7B、无 LoRA：未训练逐屏打分基线（训练效应的对照）"""
import json,torch,time,os
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'; MODEL='Qwen/Qwen2.5-7B-Instruct'
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
SET=os.environ.get('SET','')
cases=json.load(open(f'{ROOT}/scorer_cases{SET}.json')); pairs=json.load(open(f'{ROOT}/scorer_pairs{SET}.json'))
tok=AutoTokenizer.from_pretrained(MODEL); YES=tok.encode('Yes')[0]; NO=tok.encode('No')[0]
def prompt(p):
    c=cases[p['case']]; ep=c['ep']; img=ep+'_'+str(p['i'])+'.png'; early=OCR.get(img,'')[:1200]; dist=c['t']-p['i']
    return (f"You are operating an Android device.\nTask: {c['task'][:300]}\n\n[Current screen, step {c['t']}]\n{c['cur'][:800]}\n\n"
            f"[An earlier screen, {dist} steps ago (step {p['i']})]\n{early}\n\n"
            "You must now type a value that is not on the current screen. Does the earlier screen above contain that value? Answer Yes or No.")
model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='cuda'); model.eval(); res={}; t0=time.time()
with torch.no_grad():
    for j,p in enumerate(pairs):
        ids=tok.apply_chat_template([{"role":"user","content":prompt(p)}],add_generation_prompt=True,return_tensors='pt').to('cuda')
        lg=model(input_ids=ids).logits[0,-1,[YES,NO]].float(); res.setdefault(str(p['case']),{})[str(p['i'])]=torch.softmax(lg,-1)[0].item()
        if (j+1)%500==0: print(f'{j+1}/{len(pairs)} {time.time()-t0:.0f}s',flush=True)
json.dump(res,open(f'{ROOT}/scorer_untrained{SET}_probs.json','w')); print('UNTRAINED DONE',flush=True)
