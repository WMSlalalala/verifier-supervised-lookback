#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
pick(){ NEED=$1; while :; do for g in 1 0; do [ $(free_of $g) -ge $((NEED+3000)) ] && { echo $g; return; }; done; sleep 120; done; }
run(){ OUT=$1; shift; [ -s "$OUT" ] && { echo "skip $OUT"; return 0; }
  for try in 1 2 3; do G=$(pick 34000); echo "### [GPU$G try$try $(date +%H:%M)] $* ###"
    CUDA_VISIBLE_DEVICES=$G env "${@:1:$#-1}" $PY "${!#}" && return 0; sleep 180; done; echo "FAIL $OUT"; return 1; }
# ① 外部集：训练过的全历史，端到端（带历史读）
run fullhist_trained_more_hist_e2e.json SRC=trained PREFIX=fullhist SET=_more HIST=1 read_scorer.py || exit 1
# ② 主表公平化：未训练打分器也用带历史读
run scorer_untrained_hist_e2e.json SRC=untrained HIST=1 read_scorer.py || exit 1
echo "### FILL DONE ###"
