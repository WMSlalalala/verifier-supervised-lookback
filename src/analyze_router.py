"""按距离分治的可实现版本：用 P(Yes) 的分布特征决定「信逐屏打分」还是「退回全历史」。
阈值与信号均在交叉验证的训练折上选取，测试折仅用于评估 —— 避免在测试集上调参。
对照：事后上界 63.6%（知道真实 gap）、全历史 56.8%、r0 单阶段 45.8%。"""
import json, math, random, statistics
ROOT='/mnt/share/mwang49/guiodyssey'
V=[set(v) for v in json.load(open(f'{ROOT}/valid_screens.json'))]
cases=json.load(open(f'{ROOT}/cases_clean.json'))
m=json.load(open(f'{ROOT}/full_matrix_result.json')); bad=set(json.load(open(f'{ROOT}/bad_idx.json')))
keep=[i for i in range(127) if i not in bad]
B=[m['B'][i] for i in keep]          # 全历史
R0=[m['D'][i] for i in keep]         # r0 单阶段
PS=json.load(open(f'{ROOT}/eval_router_mv3_result.json'))   # 逐屏打分 + 信号
N=len(cases)
ok_ps=[PS[i][4] in V[i] for i in range(N)]
ok_b =[B[i][4]  in V[i] for i in range(N)]
ok_r0=[R0[i][4] in V[i] for i in range(N)]
SIG=['top1','margin','entropy','nscr']
def sigval(i,k):
    d=PS[i][5]
    return -d[k] if k=='entropy' else d[k]      # entropy 越低越确信 -> 取负统一为「越大越信」
print(f'n={N}')
print(f'单一方法:  逐屏打分 {100*sum(ok_ps)/N:.1f}%   全历史 {100*sum(ok_b)/N:.1f}%   r0单阶段 {100*sum(ok_r0)/N:.1f}%')
print(f'事后按真实 gap 选最优（上界）: 见 §3.16.6 = 63.6%')
print()
# 路由：sig >= thr 时信逐屏打分，否则退回全历史
def route_acc(idx, k, thr):
    return sum(1 for i in idx if (ok_ps[i] if sigval(i,k)>=thr else ok_b[i]))
def best_thr(train, k):
    cand=sorted({sigval(i,k) for i in train})
    best=(-1,None)
    for t in cand:
        a=route_acc(train,k,t)
        if a>best[0]: best=(a,t)
    return best[1]
print('=== 5-fold CV（阈值仅在训练折上选）===')
random.seed(0)
order=list(range(N)); random.shuffle(order)
folds=[order[i::5] for i in range(5)]
for k in SIG:
    tot=0
    for f in range(5):
        test=folds[f]; train=[i for i in order if i not in set(test)]
        thr=best_thr(train,k)
        tot+=route_acc(test,k,thr)
    print(f'  信号={k:<9} CV 准确率 {100*tot/N:5.1f}%')
print()
print('=== 嵌套 CV：信号与阈值均在训练折内选 ===')
tot=0; picks=[]
for f in range(5):
    test=folds[f]; train=[i for i in order if i not in set(test)]
    # 内层：在 train 上再做 4-fold 选信号
    inner=[train[i::4] for i in range(4)]
    sc={}
    for k in SIG:
        s=0
        for g in range(4):
            ite=inner[g]; itr=[i for i in train if i not in set(ite)]
            s+=route_acc(ite,k,best_thr(itr,k))
        sc[k]=s
    k=max(sc,key=sc.get); picks.append(k)
    tot+=route_acc(test,k,best_thr(train,k))
print(f'  嵌套 CV 准确率 {100*tot/N:5.1f}%   各折选中的信号: {picks}')
print()
print('=== 路由触发率与分布（用全量最优阈值，仅作描述）===')
for k in SIG:
    thr=best_thr(list(range(N)),k)
    fire=[i for i in range(N) if sigval(i,k)>=thr]
    g=[cases[i]['gap'] for i in fire]
    print(f'  {k:<9} thr={thr:+.4f}  触发 {len(fire):>3}/{N} ({100*len(fire)/N:.0f}%)  '
          f'触发集 gap 中位 {statistics.median(g) if g else float("nan"):.0f}  '
          f'全量准确率 {100*route_acc(list(range(N)),k,thr)/N:.1f}%')
print()
print('  [全量阈值为过拟合估计，真实性能以上方 CV 为准]')
print()
print('='*62)
print('=== 三选一路由：逐屏打分 / r0单阶段 / 全历史 ===')
METH={'ps':ok_ps,'r0':ok_r0,'B':ok_b}
def route3(idx,k,t1,t2):
    """sig>=t1 用逐屏; t2<=sig<t1 用 r0单阶段; sig<t2 用全历史"""
    a=0
    for i in idx:
        v=sigval(i,k)
        a+= ok_ps[i] if v>=t1 else (ok_r0[i] if v>=t2 else ok_b[i])
    return a
def best_thr3(train,k):
    cand=sorted({sigval(i,k) for i in train})
    if len(cand)<2: return cand[0],cand[0]
    step=max(1,len(cand)//20)          # 粗网格，控制搜索量
    grid=cand[::step]
    best=(-1,None,None)
    for a_ in grid:
        for b_ in grid:
            if b_>a_: continue
            acc=route3(train,k,a_,b_)
            if acc>best[0]: best=(acc,a_,b_)
    return best[1],best[2]
tot=0; detail=[]
for f in range(5):
    test=folds[f]; train=[i for i in order if i not in set(test)]
    sc={}
    for k in SIG:
        inner=[train[i::4] for i in range(4)]
        s_=0
        for g in range(4):
            ite=inner[g]; itr=[i for i in train if i not in set(ite)]
            t1,t2=best_thr3(itr,k); s_+=route3(ite,k,t1,t2)
        sc[k]=s_
    k=max(sc,key=sc.get)
    t1,t2=best_thr3(train,k)
    tot+=route3(test,k,t1,t2); detail.append(k)
print(f'  三选一 嵌套CV 准确率 {100*tot/N:5.1f}%   各折信号: {detail}')
print()
print('=== 对照汇总 ===')
print(f'  r0 单阶段（单一最优写法）     45.8%')
print(f'  全历史                       56.8%')
print(f'  二选一路由（嵌套CV）          见上')
print(f'  三选一路由（嵌套CV）          {100*tot/N:.1f}%')
print(f'  事后按真实 gap 选最优（上界）  63.6%  <- 不可引用')
