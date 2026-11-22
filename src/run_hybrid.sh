#!/bin/bash
# 混合上下文 4 组：K=2 无/有提示 × 长/短轨迹。单卡，需 >=34GB；等待+重试。
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=34000
pick(){ while :; do for g in 1 0; do u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g|tr -d ' '); [ $((49140-u)) -ge $NEED ] && { echo $g; return; }; done; echo "[$(date +%H:%M)] 等待 GPU" >&2; sleep 60; done; }
for cfg in "long 2 0" "long 2 1" "short 2 0" "short 2 1"; do
  set -- $cfg; C=$1; KK=$2; N=$3
  for try in 1 2 3 4 5 6; do
    G=$(pick); echo "### $C K=$KK NUDGE=$N on GPU$G try=$try ($(date +%H:%M)) ###"
    if CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct MODE=H K=$KK NUDGE=$N CASES=$C $PY eval_hybrid.py; then break; fi
    echo "RETRY $C K=$KK NUDGE=$N try=$try"; sleep 90
  done
done
echo "### HYBRID DONE ###"
