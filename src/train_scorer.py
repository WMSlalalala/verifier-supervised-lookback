"""逐屏打分器：Qwen2.5-7B + LoRA，输入(任务,当前屏,候选历史屏,距离)，输出 P(Yes)。FOLD=k：在其余折训练，在第 k 折打分。"""
import json,os,torch,random,math,time
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig,get_peft_model
ROOT='/mnt/share/mwang49/guiodyssey'; FOLD=os.environ['FOLD']; FOLD=int(FOLD) if FOLD!='ext' else 'ext'; MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-7B-Instruct')
TAG=os.environ.get('TAG',''); NODIST=os.environ.get('NODIST','0')=='1'
EPOCHS=int(os.environ.get('EPOCHS','2')); LR=float(os.environ.get('LR','1e-4')); ACC=4; POSW=float(os.environ.get('POSW','3'))
OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/scorer_cases.json')); pairs=json.load(open(f'{ROOT}/scorer_pairs.json'))
if FOLD=='ext':
    cases_more=json.load(open(f'{ROOT}/scorer_cases_more.json')); pairs_more=json.load(open(f'{ROOT}/scorer_pairs_more.json'))
    off=len(cases); cases=cases+cases_more
    for p in pairs_more: p['case']+=off; p['fold']='ext'
    pairs=pairs+pairs_more
tok=AutoTokenizer.from_pretrained(MODEL); YES=tok.encode('Yes')[0]; NO=tok.encode('No')[0]
def prompt(p):
    c=cases[p['case']]; ep=c['ep']; img=ep+'_'+str(p['i'])+'.png'; early=OCR.get(img,'')[:1200]; dist=c['t']-p['i']
    hdr=(f"[An earlier screen]" if NODIST else f"[An earlier screen, {dist} steps ago (step {p['i']})]")
    return (f"You are operating an Android device.\nTask: {c['task'][:300]}\n\n[Current screen, step {c['t']}]\n{c['cur'][:800]}\n\n"
            f"{hdr}\n{early}\n\n"
            "You must now type a value that is not on the current screen. Does the earlier screen above contain that value? Answer Yes or No.")
def enc(p):
    ids=tok.apply_chat_template([{"role":"user","content":prompt(p)}],add_generation_prompt=True,return_tensors='pt')
    return ids
model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,device_map='cuda'); model.gradient_checkpointing_enable(); model.enable_input_require_grads()
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
train=[p for p in pairs if p['fold']!=FOLD]; test=[p for p in pairs if p['fold']==FOLD]
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=LR,weight_decay=0.0)
steps=EPOCHS*len(train)//ACC; sched=torch.optim.lr_scheduler.LambdaLR(opt,lambda s:max(0.0,1-s/max(steps,1)))
model.train(); random.seed(FOLD); t0=time.time(); n=0; tot=0.0
for ep in range(EPOCHS):
    random.shuffle(train)
    for j,p in enumerate(train):
        ids=enc(p).to('cuda'); out=model(input_ids=ids); lg=out.logits[0,-1,[YES,NO]].float()
        logp=torch.log_softmax(lg,-1); w=POSW if p['label'] else 1.0
        loss=-w*logp[0 if p['label'] else 1]/ACC; loss.backward(); tot+=loss.item()*ACC; n+=1
        if (j+1)%ACC==0: torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); sched.step(); opt.zero_grad()
        if n%400==0: print(f'fold{FOLD} ep{ep} {n}/{EPOCHS*len(train)} loss {tot/400:.3f} {time.time()-t0:.0f}s',flush=True); tot=0.0
model.eval(); res={}
with torch.no_grad():
    for p in test:
        ids=enc(p).to('cuda'); lg=model(input_ids=ids).logits[0,-1,[YES,NO]].float(); pr=torch.softmax(lg,-1)[0].item()
        res.setdefault(p['case'],{})[p['i']]=pr
json.dump(res,open(f'{ROOT}/scorer{TAG}_fold{FOLD}_probs.json','w')); print(f'FOLD_DONE {FOLD} cases {len(res)} {time.time()-t0:.0f}s',flush=True)
