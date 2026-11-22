"""Writer DPO 训练：让 writer 朝着「reader 能据此定位」的方向优化

数据来自 oracle_directory_result.json：
  chosen   = 使 reader 定位成功的候选条目
  rejected = 未能使 reader 定位成功的候选条目
这正是 proposal 的核心机制——writer 的训练信号直接来自 reader 的检索成功率。

LoRA + 手写 DPO loss（reference = 禁用 adapter 的同一模型，省一份显存）
"""
import json, os, random, math, time, torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-7B-Instruct')
EPOCHS=int(os.environ.get('EPOCHS','3')); LR=float(os.environ.get('LR','1e-4'))
BETA=float(os.environ.get('BETA','0.1')); BS=int(os.environ.get('BS','2'))
OUT=f'{ROOT}/writer_lora'
random.seed(0); torch.manual_seed(0)

PROMPT=("Below is the text extracted from one Android screen.\n\n{txt}\n\n"
        "Write ONE short directory line (max 20 words) that will later help someone "
        "DECIDE WHETHER TO RE-OPEN THIS SCREEN when they need a specific value. "
        "Name the screen type and WHICH KINDS OF VALUES it contains — do not list the values themselves.\n"
        "Output ONLY the line.")

pairs=json.load(open(f'{ROOT}/dpo_pairs.json'))
random.shuffle(pairs)
n_val=max(16,len(pairs)//10); val=pairs[:n_val]; train=pairs[n_val:]
print(f'train {len(train)}  val {len(val)}', flush=True)

tok=AutoTokenizer.from_pretrained(MODEL)
tok.padding_side='right'
if tok.pad_token is None: tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto')
model.config.use_cache=False
model=get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
    task_type='CAUSAL_LM', target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
model.print_trainable_parameters()
dev=next(model.parameters()).device

def encode(ex, resp):
    msgs=[{"role":"user","content":PROMPT.format(txt=ex['screen'])}]
    p=tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    pi=tok(p, add_special_tokens=False)['input_ids']
    ri=tok(resp+tok.eos_token, add_special_tokens=False)['input_ids']
    return pi+ri, len(pi)

def seq_logp(ids_list, plens, use_ref=False):
    """返回每条序列在 response 部分的 log prob 之和"""
    L=max(len(x) for x in ids_list)
    inp=torch.full((len(ids_list),L), tok.pad_token_id, dtype=torch.long)
    msk=torch.zeros((len(ids_list),L), dtype=torch.long)
    for i,x in enumerate(ids_list):
        inp[i,:len(x)]=torch.tensor(x); msk[i,:len(x)]=1
    inp=inp.to(dev); msk=msk.to(dev)
    ctx = model.disable_adapter() if use_ref else torch.enable_grad()
    with ctx:
        out=model(input_ids=inp, attention_mask=msk).logits
    lp=F.log_softmax(out[:,:-1].float(), dim=-1)
    tgt=inp[:,1:]
    tokmask=torch.zeros_like(tgt, dtype=torch.bool)
    for i,x in enumerate(ids_list):
        tokmask[i, plens[i]-1:len(x)-1]=True
    g=lp.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
    return (g*tokmask).sum(-1)

def batch_loss(batch, grad=True):
    ids=[]; pl=[]
    for ex in batch:
        a,la=encode(ex,ex['chosen']);  ids.append(a); pl.append(la)
    for ex in batch:
        b,lb=encode(ex,ex['rejected']); ids.append(b); pl.append(lb)
    pol=seq_logp(ids,pl,use_ref=False)
    with torch.no_grad(): ref=seq_logp(ids,pl,use_ref=True)
    k=len(batch)
    logits=BETA*((pol[:k]-ref[:k])-(pol[k:]-ref[k:]))
    loss=-F.logsigmoid(logits).mean()
    acc=(logits>0).float().mean().item()
    return loss, acc

opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
steps=math.ceil(len(train)/BS)*EPOCHS
sch=torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, total_steps=steps, pct_start=0.1)
t0=time.time(); gstep=0
for ep in range(EPOCHS):
    model.train(); random.shuffle(train)
    for i in range(0,len(train),BS):
        b=train[i:i+BS]
        loss,acc=batch_loss(b)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        opt.step(); sch.step(); opt.zero_grad(); gstep+=1
        if gstep%20==0: print(f'  ep{ep} step{gstep}/{steps} loss={loss.item():.4f} acc={acc:.2f} {time.time()-t0:.0f}s', flush=True)
    model.eval(); vl=[]; va=[]
    with torch.no_grad():
        for i in range(0,len(val),BS):
            l,a=batch_loss(val[i:i+BS], grad=False); vl.append(l.item()); va.append(a)
    print(f'== epoch {ep}: val_loss={sum(vl)/len(vl):.4f} val_acc={sum(va)/len(va):.3f}  {time.time()-t0:.0f}s', flush=True)
model.save_pretrained(OUT)
print(f'saved -> {OUT}')
