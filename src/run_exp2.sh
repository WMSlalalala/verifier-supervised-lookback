#!/bin/bash
# 续跑：显存守卫 + 失败重试，不挤占他人任务
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
# 等到某卡空余 >= NEED，返回卡号；预留 3G 余量给他人
pick(){ NEED=$1; while :; do for g in 0 1; do [ $(free_of $g) -ge $((NEED+3000)) ] && { echo $g; return; }; done; sleep 120; done; }
run(){ # run <need> <outfile> <env...> <script>
  NEED=$1; OUT=$2; shift 2
  [ -s "$OUT" ] && { echo "skip $OUT"; return 0; }
  for try in 1 2 3 4 5 6 7 8; do
    G=$(pick $NEED); echo "### [GPU$G try$try $(date +%H:%M)] $* ###"
    if CUDA_VISIBLE_DEVICES=$G env "${@:1:$#-1}" $PY "${!#}"; then return 0; fi
    echo "RETRY $OUT try=$try"; sleep 180
  done; echo "FAIL $OUT"; return 1; }
echo "===== A 训练过的全历史基线（续 fold4）====="
for f in 0 1 2 3 4; do run 26000 fullhist_fold${f}_probs.json FOLD=$f train_fullhist.py || exit 1; done
echo "===== C top-2 读取（先做，短）====="
run 34000 scorer_trained_hist_top2_e2e.json SRC=trained HIST=1 MARK=top2 read_scorer.py || exit 1
echo "===== B1 消融：去掉距离 ====="
for f in 0 1 2 3 4; do run 26000 scorer_nodist_fold${f}_probs.json FOLD=$f TAG=_nodist NODIST=1 train_scorer.py || exit 1; done
echo "===== B2 消融：正例权重=1 ====="
for f in 0 1 2 3 4; do run 26000 scorer_posw1_fold${f}_probs.json FOLD=$f TAG=_posw1 POSW=1 train_scorer.py || exit 1; done
echo "===== B3 消融：3B ====="
for f in 0 1 2 3 4; do run 16000 scorer_3B_fold${f}_probs.json FOLD=$f TAG=_3B MODEL=Qwen/Qwen2.5-3B-Instruct train_scorer.py || exit 1; done
echo "### EXP2 DONE ###"
