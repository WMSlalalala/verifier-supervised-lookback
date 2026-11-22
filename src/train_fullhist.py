"""训练过的全历史基线：同样的验证器标签，LoRA SFT 让 7B 在全历史 prompt 下直接输出源屏编号。FOLD=k 五折。输出与打分器同格式的 probs（pred->1.0）。"""
import json,os,torch,random,time,re
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig,get_peft_model
ROOT='/mnt/share/mwang49/guiodyssey'; FOLD=os.environ['FOLD']; FOLD=int(FOLD) if FOLD!='ext' else 'ext'; MODEL='Qwen/Qwen2.5-7B-Instruct'; EPOCHS=2; LR=1e-4; ACC=4
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/scorer_cases.json'))
if FOLD=='ext':
    more=json.load(open(f'{ROOT}/scorer_cases_more.json'))
    for c in more: c['fold']='ext'
    cases=cases+more
tok=AutoTokenizer.from_pretrained(MODEL)
def prompt(c):
    ep,t=c['ep'],c['t']; hist=''.join(f"Screen {i}: {OCR.get(f'{ep}_{i}.png','')[:700]}\n" for i in range(t) if OCR.get(f'{ep}_{i}.png'))
    return (f"You are operating an Android device.\nTask: {c['task'][:300]}\n\n[All screens you saw earlier]\n{hist}\n[Current screen, step {t}]\n{c['cur'][:800]}\n\n"
            "You must now type a value that is not on the current screen but appeared on one earlier screen. Which earlier screen holds it? Answer with the screen number only.")
model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='cuda'); model.gradient_checkpointing_enable(); model.enable_input_require_grads()
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
train=[c for c in cases if c['fold']!=FOLD]; test=[(i,c) for i,c in enumerate(cases) if c['fold']==FOLD]
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=LR); model.train(); random.seed(FOLD); t0=time.time(); n=0
for ep in range(EPOCHS):
    random.shuffle(train)
    for j,c in enumerate(train):
        tgt=str(max(c['valid']))
        pids=tok.apply_chat_template([{"role":"user","content":prompt(c)}],add_generation_prompt=True,return_tensors='pt')[0]
        tids=torch.tensor(tok.encode(tgt+tok.eos_token,add_special_tokens=False))
        ids=torch.cat([pids,tids]).unsqueeze(0).to('cuda'); labels=ids.clone(); labels[0,:len(pids)]=-100
        loss=model(input_ids=ids,labels=labels).loss/ACC; loss.backward(); n+=1
        if (j+1)%ACC==0: torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); opt.zero_grad()
        if n%50==0: print(f'fullhist fold{FOLD} ep{ep} {n}/{EPOCHS*len(train)} {time.time()-t0:.0f}s',flush=True)
model.eval(); res={}
with torch.no_grad():
    for i,c in test:
        ids=tok.apply_chat_template([{"role":"user","content":prompt(c)}],add_generation_prompt=True,return_tensors='pt').to('cuda')
        o=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=5,do_sample=False,pad_token_id=tok.eos_token_id)
        txt=tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True); m=re.search(r'\d+',txt); pred=int(m.group()) if m else -1
        res[i]={pred:1.0}
json.dump(res,open(f'{ROOT}/fullhist_fold{FOLD}_probs.json','w')); print(f'FULLHIST FOLD_DONE {FOLD} {time.time()-t0:.0f}s',flush=True)
