#!/bin/bash
# K 扫描（无提示，长轨迹）：等 run_hybrid.sh 结束后接着跑 K=1, K=3
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=34000
while ! grep -q "HYBRID DONE" hybrid.log 2>/dev/null; do sleep 30; done
pick(){ while :; do for g in 1 0; do u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g|tr -d ' '); [ $((49140-u)) -ge $NEED ] && { echo $g; return; }; done; echo "[$(date +%H:%M)] 等待 GPU" >&2; sleep 60; done; }
for KK in 1 3; do
  for try in 1 2 3 4 5 6; do
    G=$(pick); echo "### long K=$KK NUDGE=0 on GPU$G try=$try ($(date +%H:%M)) ###"
    if CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct MODE=H K=$KK NUDGE=0 CASES=long $PY eval_hybrid.py; then break; fi
    echo "RETRY K=$KK try=$try"; sleep 90
  done
done
echo "### KSWEEP DONE ###"
