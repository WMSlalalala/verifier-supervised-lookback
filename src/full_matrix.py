"""完整基线矩阵：延迟信息需求的两阶段 pipeline 评估

每个条件都跑真实 pipeline：
  stage1 定位 -> 预测源屏 pred
  stage2 读取 -> 用【预测的】那一屏（不是 oracle）去读值
  端到端 = 两阶段都对

条件：
  A no-history        task + 当前屏                     下界
  B full-history      task + 全历史 verbatim + 当前屏    强基线
  C rolling-summary   task + 滚动摘要 + 当前屏           GUI-Rise 式
  D directory-r0      task + 目录(prompt-only) + 当前屏  ReadAgent 式
  E dir+retrieve      目录定位 -> 取回该屏全文 -> 读      ★完整三层
附加：
  oracle-read         给定真源屏读值                     读取上界
"""
import json, os, re, torch, collections, time
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT='/mnt/share/mwang49/guiodyssey'
MODEL=os.environ.get('MODEL','Qwen/Qwen2.5-14B-Instruct')
LIMIT=int(os.environ.get('LIMIT','0'))
def norm(s): return re.sub(r'[\s,，.。]','',(s or '').lower())

OCR={}
for ln in open(f'{ROOT}/parse_odyssey.jsonl'):
    d=json.loads(ln); OCR[d['img']]=' '.join(x['t'] for x in d['elems'] if x.get('t'))
DIR={}
for ln in open(f'{ROOT}/directory_r0.jsonl'):
    try: d=json.loads(ln); DIR[d['img']]=d['entry']
    except Exception: pass
cases=json.load(open(f'{ROOT}/cases.json'))
if LIMIT: cases=cases[:LIMIT]
anno={}
for c in cases:
    if c['ep'] not in anno: anno[c['ep']]=json.load(open(f"{ROOT}/annotations/{c['ep']}.json"))

print(f'loading {MODEL} ...', flush=True); t0=time.time()
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map='auto'); model.eval()
print(f'loaded in {time.time()-t0:.0f}s', flush=True)

def gen(p, n=24):
    ids=tok.apply_chat_template([{"role":"user","content":p}], add_generation_prompt=True, return_tensors='pt').to(model.device)
    with torch.no_grad():
        o=model.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=n,
                         do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip(), ids.shape[1]

# ---------- 滚动摘要（条件 C）----------
SUM_F=f'{ROOT}/summaries.json'
if os.path.exists(SUM_F):
    SUMM=json.load(open(SUM_F)); print(f'滚动摘要已存在 {len(SUMM)}', flush=True)
else:
    SUMM={}
    todo=sorted({(c['ep'],c['t']) for c in cases})
    # 一次性摘要：看完全部历史再压缩。这【强于】GUI-Rise 式滚动摘要
    # （后者写摘要时不知道未来），所以它的失败同时否定了摘要方案的上界。
    for k,(ep,t) in enumerate(todo):
        rows=[f"Screen {i}: {OCR[f'{ep}_{i}.png']}" for i in range(t) if OCR.get(f'{ep}_{i}.png')]
        pr=(f"Task: {anno[ep]['task_info']['task']}\n\n"
            f"[All screens seen so far]\n"+"\n".join(rows)+
            f"\n\nWrite a summary of what has happened so far that will be carried forward "
            f"INSTEAD of these screens. Keep it under 80 words. Output ONLY the summary.")
        sm,_=gen(pr, 130)
        SUMM[f'{ep}_{t}']=sm
        if (k+1)%25==0: print(f'  [summary] {k+1}/{len(todo)}  {time.time()-t0:.0f}s', flush=True)
    json.dump(SUMM, open(SUM_F,'w'), ensure_ascii=False, indent=1)
    print(f'摘要完成(一次性/强设定) -> {SUM_F}', flush=True)

# ---------- prompt 构造 ----------
def hist_block(c, cond):
    ep,t=c['ep'],c['t']
    if cond=='A': return None
    if cond=='B':
        rows=[f"Screen {i}: {OCR[f'{ep}_{i}.png']}" for i in range(t) if OCR.get(f'{ep}_{i}.png')]
        return "[Screens you have already seen]\n"+"\n".join(rows)
    if cond=='C':
        return f"[Summary of what you have done so far]\n{SUMM.get(f'{ep}_{t}','')}"
    if cond in ('D','E'):
        rows=[f"Screen {i}: {DIR[f'{ep}_{i}.png']}" for i in range(t) if DIR.get(f'{ep}_{i}.png')]
        return "[Index of screens you have already seen]\n"+"\n".join(rows)

def p_locate(c, cond):
    ep,t=c['ep'],c['t']
    return (f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
            f"{hist_block(c,cond)}\n\n[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
            f"On the current screen you must type something into an input field. "
            f"The value you need was visible on exactly ONE of the earlier screens.\n"
            f"Which earlier screen number contains it? Answer with ONLY the number.")

def p_read(c, src, cond):
    """各条件 stage2 看到的历史表示不同：
       A 无历史 | B 全历史全文 | C 滚动摘要 | D 只有目录条目(纯gist,不取回) | E/F 取回该屏全文"""
    ep,t=c['ep'],c['t']
    if cond=='A':
        ctx=""
    elif cond=='B':
        rows=[f"Screen {i}: {OCR[f'{ep}_{i}.png']}" for i in range(t) if OCR.get(f'{ep}_{i}.png')]
        ctx="[Screens you have already seen]\n"+"\n".join(rows)+"\n\n"
    elif cond=='C':
        ctx=f"[Summary of what you have done so far]\n{SUMM.get(f'{ep}_{t}','')}\n\n"
    elif cond=='D':
        if src is None or src<0: ctx=""
        else: ctx=f"[The index entry for an earlier screen]\nScreen {src}: {DIR.get(f'{ep}_{src}.png','')}\n\n"
    else:   # E, F -> 取回原文
        if src is None or src<0: ctx=""
        else: ctx=f"[A screen you saw earlier]\nScreen {src}: {OCR.get(f'{ep}_{src}.png','')}\n\n"
    return (f"You are operating an Android device.\n\nTask: {anno[ep]['task_info']['task']}\n\n"
            f"{ctx}[Current screen {t}]\n{OCR.get(f'{ep}_{t}.png','')}\n\n"
            f"What exact text should you type now? Answer with ONLY that text.")

CONDS=['A','B','C','D','E']
R=collections.defaultdict(list)
for cond in CONDS:
    for k,c in enumerate(cases):
        if cond=='A':
            pred=-1; ctx1=0
        else:
            o,ctx1=gen(p_locate(c,cond),8)
            m=re.search(r'\d+',o); pred=int(m.group()) if m else -1
        loc_ok = (pred==c['src'])
        # stage2: 用【预测的】屏去读（E 条件 = 取回全文；D 条件也取回，区别在定位用的是目录）
        o2,_=gen(p_read(c, pred, cond),24)
        read_ok = norm(c['ans']) in norm(o2)
        R[cond].append((loc_ok, read_ok, c['gap'], c['src'], pred, ctx1))
        if (k+1)%40==0: print(f'  [{cond}] {k+1}/{len(cases)}  {time.time()-t0:.0f}s', flush=True)
    r=R[cond]
    print(f'== {cond}: 定位 {100*sum(1 for x in r if x[0])/len(r):.1f}%  '
          f'端到端 {100*sum(1 for x in r if x[1])/len(r):.1f}%  '
          f'ctx {sum(x[5] for x in r)/len(r):.0f}tok', flush=True)

# oracle 读取上界
orc=[]
for c in cases:
    o,_=gen(p_read(c,c['src'],'F'),24)
    orc.append(norm(c['ans']) in norm(o))

NAMES={'A':'A no-history      (无历史, 纯任务语义猜)','B':'B full-history    (全历史原文, 定位+读都有)',
       'C':'C summary        (一次性摘要, 强于GUI-Rise)','D':'D directory-only  (纯目录, 不取回原文)',
       'E':'E dir+retrieve    (目录定位->取回原文->读) *'}
print('\n'+'='*78)
print(f'MODEL={MODEL}  n={len(cases)}')
print(f"{'条件':<46}{'定位R@1':>9}{'端到端':>9}{'ctx':>8}")
for cond in CONDS:
    r=R[cond]
    print(f"{NAMES[cond]:<46}{100*sum(1 for x in r if x[0])/len(r):>8.1f}%{100*sum(1 for x in r if x[1])/len(r):>8.1f}%{sum(x[5] for x in r)/len(r):>7.0f}")
print(f"{'F oracle-read     (给定真源屏读值)':<46}{'—':>9}{100*sum(orc)/len(orc):>8.1f}%{'—':>8}")
print(f"\n参考: BM25-ctx R@1=11.8%   BM25-oracle R@1=65.4%")
print('\n=== 按 gap 分组（定位 R@1）===')
print(f"{'gap':<8}{'n':>5}" + "".join(f"{c:>8}" for c in CONDS))
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[i for i,x in enumerate(R['B']) if lo<=x[2]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}" + "".join(f"{100*sum(1 for i in idx if R[c][i][0])/len(idx):>7.0f}%" for c in CONDS))
print('\n=== 按 gap 分组（端到端）===')
print(f"{'gap':<8}{'n':>5}" + "".join(f"{c:>8}" for c in CONDS))
for lo,hi in [(1,2),(3,4),(5,7),(8,100)]:
    idx=[i for i,x in enumerate(R['B']) if lo<=x[2]<=hi]
    if not idx: continue
    lab=f'{lo}-{hi}' if hi<100 else f'{lo}+'
    print(f"{lab:<8}{len(idx):>5}" + "".join(f"{100*sum(1 for i in idx if R[c][i][1])/len(idx):>7.0f}%" for c in CONDS))
json.dump({c:R[c] for c in R} | {'oracle_read':orc,'model':MODEL},
          open(f'{ROOT}/full_matrix_result.json','w'), ensure_ascii=False, indent=1)
print(f'\n-> {ROOT}/full_matrix_result.json')
