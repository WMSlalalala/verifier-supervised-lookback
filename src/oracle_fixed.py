"""[修正指标版] 定位正确 = pred 落在任一含答案屏；同时记录严格指标以便对照。
Layer 2 上界：如果目录条目写得「完美」，定位能到多少？

对每个 case 的每一个历史帧，生成 M 个候选目录条目；
用 reader 逐个试（只替换源屏的条目，其余保持 r0），
记录哪个候选能让 reader 定位成功 + token 成本。

  oracle-dir  = 存在至少一个候选使 reader 定位成功的比例  -> Layer2 上界
  r0-dir      = 用 prompt-only 的 r0 条目                -> 现状
  差值        = 训练 writer 能争取到的空间

这比直接 SFT 便宜得多，且先回答「目录这个形式有没有天花板」。
"""
import json, os, re, torch, collections, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
LIMIT=int(os.environ.get('LIMIT','0')); M=int(os.environ.get('M','4'))
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
DIR={}
for ln in open(f'{ROOT}/directory_r0.jsonl'):
    try: d=json.loads(ln); DIR[d['img']]=d['entry']
    except Exception: pass
cases=json.load(open(f'{ROOT}/cases_clean.json'))
VALID=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
if LIMIT: cases=cases[:LIMIT]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))

print(f'loading {MODEL} ...', flush=True); t0=time.time()
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()
print(f'loaded in {time.time()-t0:.0f}s', flush=True)

def gen(p, n=40, sample=False):
    ids=tok.apply_chat_template([{"role":"user","content":p}], add_generation_prompt=True, return_tensors='pt').to(model.device)
    kw=dict(max_new_tokens=n, pad_token_id=tok.eos_token_id, attention_mask=torch.ones_like(ids))
    kw.update(dict(do_sample=True, temperature=0.9, top_p=0.95) if sample else dict(do_sample=False))
    with torch.no_grad(): o=model.generate(ids, **kw)
    return tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip()

CAND_P=("Below is the text extracted from one Android screen.\n\n{txt}\n\n"
        "Write ONE short directory line (max 20 words) that will later help someone "
        "DECIDE WHETHER TO RE-OPEN THIS SCREEN when they need a specific value. "
        "Name the screen type and WHICH KINDS OF VALUES it contains — do not list the values themselves.\n"
        "Output ONLY the line.")

def p_locate(c, dir_override=None):
    ep,t=c['ep'],c['t']
    rows=[]
    for i in range(t):
        k=f'{ep}_{i}.png'
        if k not in DIR: continue
        e = dir_override if (dir_override is not None and i==c['src']) else DIR[k]
        rows.append(f"Screen {i}: {e}")
    return (f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
            f"[Index of screens you have already seen]\n"+"\n".join(rows)+
            f"\n\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
            f"On the current screen you must type something into an input field. "
            f"The value you need was visible on exactly ONE of the earlier screens.\n"
            f"Which earlier screen number contains it? Answer with ONLY the number.")

def locate(c, override=None):
    o=gen(p_locate(c,override),8)
    m=re.search(r'\d+',o); return (int(m.group()) if m else -1)

res=[]
for k,c in enumerate(cases):
    src_img=f"{c['ep']}_{c['src']}.png"
    VS=VALID[k]                      # k = case 索引（勿与候选索引混用）
    bp=locate(c)
    base_ok=(bp in VS); base_strict=(bp==c['src'])
    txt=OCR.get(src_img,'')[:2500]
    cands=[DIR.get(src_img,'')]
    for _ in range(M):
        cands.append(gen(CAND_P.format(txt=txt), 40, sample=True).split('\n')[0][:160])
    hits=[]; hits_strict=[]; preds=[]
    for cj,cd in enumerate(cands):
        if not cd:
            hits.append(False); hits_strict.append(False); preds.append(-1); continue
        p=locate(c, cd)
        preds.append(p); hits.append(p in VS); hits_strict.append(p==c['src'])
    res.append({'ep':c['ep'],'t':c['t'],'src':c['src'],'gap':c['gap'],
                'base_ok':base_ok,'base_strict':base_strict,'base_pred':bp,
                'cand_hits':hits,'cand_hits_strict':hits_strict,'preds':preds,'cands':cands,
                'oracle_ok':any(hits),'oracle_strict':any(hits_strict),'n_hit':sum(hits)})
    if (k+1)%20==0:
        r=res; print(f'  {k+1}/{len(cases)}  base={100*sum(1 for x in r if x["base_ok"])/len(r):.0f}% '
                     f'oracle={100*sum(1 for x in r if x["oracle_ok"])/len(r):.0f}%  {time.time()-t0:.0f}s', flush=True)

n=len(res)
print('\n'+'='*70)
print(f'MODEL={MODEL}  n={n}  候选数/帧={M+1}(含r0)')
print(f"r0 目录（prompt-only）定位 R@1          {100*sum(1 for x in res if x['base_ok'])/n:5.1f}%")
print(f"oracle 目录（M+1 候选中存在可用的）      {100*sum(1 for x in res if x['oracle_ok'])/n:5.1f}%   <- Layer2 上界")
print(f"  平均可用候选数                        {sum(x['n_hit'] for x in res)/n:.2f} / {M+1}")
print(f"  从失败翻盘的 case                      {sum(1 for x in res if not x['base_ok'] and x['oracle_ok'])}")
print(f"  r0 成功但多数候选失败的 case            {sum(1 for x in res if x['base_ok'] and x['n_hit']<=1)}")
print('\n=== 按 gap ===')
print(f"{'gap':<8}{'n':>5}{'r0':>8}{'oracle':>9}")
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[x for x in res if lo<=x['gap']<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}{100*sum(1 for x in idx if x['base_ok'])/len(idx):>7.0f}%{100*sum(1 for x in idx if x['oracle_ok'])/len(idx):>8.0f}%")
json.dump(res, open(f'{ROOT}/oracle_fixed_result.json','w'), ensure_ascii=False, indent=1)
print(f'\n-> {ROOT}/oracle_fixed_result.json')
