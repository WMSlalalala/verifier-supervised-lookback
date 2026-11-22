"""核心问题：把全历史 verbatim 文本给强 LLM，它能定位到正确的源屏吗？

实验1 定位(主)  输入 task+当前屏+全部历史屏(编号) -> 输出屏号
                 与 BM25-ctx R@1=11.8% 直接可比
实验2 读取(辅)  输入 task+当前屏+【正确源屏】 -> 输出要填的文本
                 测"知道去哪看之后能不能读对"= 端到端上界
"""
import json, os, re, torch, collections
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
LIMIT=int(os.environ.get('LIMIT','0'))
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
cases=json.load(open(f'{ROOT}/cases.json'))
if LIMIT: cases=cases[:LIMIT]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))

def p_locate(c):
    ep,t=c['ep'],c['t']; task=anno[ep]['task_info']['task']
    hist=[f"Screen {i}: {OCR[f'{ep}_{i}.png']}" for i in range(t) if OCR.get(f'{ep}_{i}.png')]
    return (f"You are operating an Android device.\n\nTask: {task}\n\n"
            f"[Screens you have already seen]\n" + "\n".join(hist) +
            f"\n\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
            f"On the current screen you must type something into an input field. "
            f"The value you need was visible on exactly ONE of the earlier screens.\n"
            f"Which earlier screen number contains it? Answer with ONLY the number."), hist

def p_read(c):
    ep,t,src=c['ep'],c['t'],c['src']; task=anno[ep]['task_info']['task']
    return (f"You are operating an Android device.\n\nTask: {task}\n\n"
            f"[A screen you saw earlier]\nScreen {src}: {OCR.get(f'{ep}_{src}.png','')}\n\n"
            f"[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
            f"The value you must now type is present on screen {src}. "
            f"What exact text should you type? Answer with ONLY that text.")

print(f'loading {MODEL} ...', flush=True)
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()
def gen(p, n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}], add_generation_prompt=True, return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=n,
                         do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip(), ids.shape[1]

loc=[]; rd=[]
for k,c in enumerate(cases):
    p,hist=p_locate(c); out,ctx=gen(p,8)
    m=re.search(r'\d+', out); pred=int(m.group()) if m else -1
    loc.append((pred==c['src'], c['gap'], c['src'], pred, c['t'], ctx))
    out2,_=gen(p_read(c),24)
    rd.append((norm(c['ans']) in norm(out2), c['gap'], c['ans'], out2))
    if (k+1)%20==0: print(f'  {k+1}/{len(cases)}', flush=True)

print('\n'+'='*64)
print(f'MODEL={MODEL}  n={len(cases)}')
a1=100*sum(1 for x in loc if x[0])/len(loc)
a2=100*sum(1 for x in rd if x[0])/len(rd)
print(f'实验1 定位 R@1（全历史, LLM）      {a1:5.1f}%     [BM25-ctx 对照 11.8%]')
print(f'实验2 读取 acc（已知源屏）         {a2:5.1f}%')
print(f'  平均 context                    {sum(x[5] for x in loc)/len(loc):.0f} tok')
print(f'  平均历史屏数                    {sum(x[4] for x in loc)/len(loc):.1f}')
print('\n=== 定位准确率 vs gap ===')
print(f"{'gap':<8}{'n':>5}{'定位R@1':>10}{'读取acc':>10}")
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[i for i,x in enumerate(loc) if lo<=x[1]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}{100*sum(1 for i in idx if loc[i][0])/len(idx):>9.0f}%{100*sum(1 for i in idx if rd[i][0])/len(idx):>9.0f}%")
json.dump({'locate':loc,'read':rd,'model':MODEL}, open(f'{ROOT}/fullhist_locate_result.json','w'), ensure_ascii=False, indent=1)
print(f'\n-> {ROOT}/fullhist_locate_result.json')
