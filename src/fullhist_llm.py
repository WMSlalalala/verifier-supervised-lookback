"""全历史 verbatim 文本 + 强 LLM 能不能答对延迟信息需求？

三组对照（都严格 i<t）：
  A no-history   task + 当前屏            -> 下界（证明确实需要历史）
  B full-history task + 全部历史屏 + 当前屏 -> ★ 要测的强基线
  C oracle-src   task + 源屏 + 当前屏       -> 上界（知道去哪看时的天花板）
判定：归一化后答案串出现在模型输出中
"""
import json, os, re, sys, torch, collections
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
LIMIT=int(os.environ.get('LIMIT','0'))
os.environ.setdefault('HF_HOME','/mnt/share/mwang49/hf_cache')

def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/cases.json'))
if LIMIT: cases=cases[:LIMIT]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))

def build(c, mode):
    ep,t,src=c['ep'],c['t'],c['src']
    task=anno[ep]['task_info']['task']
    cur=OCR.get(f'{ep}_{t}.png','')
    parts=[f"You are operating an Android device to complete a task.\n\nTask: {task}\n"]
    if mode=='B':
        parts.append("[Screens you have seen so far]")
        for i in range(t):
            txt=OCR.get(f'{ep}_{i}.png')
            if txt: parts.append(f"Screen {i}: {txt}")
        parts.append("")
    elif mode=='C':
        parts.append(f"[An earlier screen]\nScreen {src}: {OCR.get(f'{ep}_{src}.png','')}\n")
    parts.append(f"[Current screen]\nScreen {t}: {cur}\n")
    parts.append("You now need to type text into an input field on the current screen. "
                 "Based on the task and what you have seen, what exact text should you type?\n"
                 "Answer with ONLY the text to type, nothing else.")
    return "\n".join(parts)

print(f'loading {MODEL} ...', flush=True)
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map='auto')
model.eval()

res=collections.defaultdict(list)
for mi,mode in enumerate(['A','B','C']):
    for k,c in enumerate(cases):
        p=build(c,mode)
        msgs=[{"role":"user","content":p}]
        ids=tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors='pt').to(model.device)
        with torch.no_grad():
            out=model.generate(ids, max_new_tokens=32, do_sample=False,
                               pad_token_id=tok.eos_token_id)
        ans=tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
        ok = norm(c['ans']) in norm(ans)
        res[mode].append((ok, c['gap'], c['ans'], ans, ids.shape[1]))
        if (k+1)%25==0: print(f'  [{mode}] {k+1}/{len(cases)}', flush=True)

print('\n'+'='*62)
print(f'MODEL={MODEL}  n={len(cases)}')
names={'A':'A no-history  (task+当前屏)','B':'B FULL-HISTORY(task+全历史+当前屏)','C':'C oracle-src  (task+源屏+当前屏)'}
for mode in ['A','B','C']:
    r=res[mode]; acc=100*sum(1 for x in r if x[0])/len(r)
    ctx=sum(x[4] for x in r)/len(r)
    print(f'{names[mode]:<40} acc={acc:5.1f}%   平均context={ctx:.0f} tok')
print('\n=== 按 gap 分组准确率 ===')
bins=[(1,2),(3,4),(5,7),(8,100)]
print(f"{'gap':<10}{'n':>5}{'A':>8}{'B':>8}{'C':>8}")
for lo,hi in bins:
    idx=[i for i,x in enumerate(res['A']) if lo<=x[1]<=hi]
    if not idx: continue
    row=[100*sum(1 for i in idx if res[m][i][0])/len(idx) for m in ['A','B','C']]
    lab = f"{lo}-{hi}" if hi < 100 else f"{lo}+"
    print(f"{lab:<10}{len(idx):>5}{row[0]:>7.0f}%{row[1]:>7.0f}%{row[2]:>7.0f}%")
json.dump({m:[(o,g,a,p) for o,g,a,p,_ in res[m]] for m in res},
          open(f'{ROOT}/fullhist_llm_result.json','w'), ensure_ascii=False, indent=1)
print(f'\n-> {ROOT}/fullhist_llm_result.json')
