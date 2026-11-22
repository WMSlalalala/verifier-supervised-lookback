#!/bin/bash
# 两段式 reader（长轨迹 K=2），等 K 扫描结束后跑
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=34000
while ! grep -q "KSWEEP DONE" ksweep.log 2>/dev/null; do sleep 30; done
pick(){ while :; do for g in 1 0; do u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g|tr -d ' '); [ $((49140-u)) -ge $NEED ] && { echo $g; return; }; done; echo "[$(date +%H:%M)] 等待 GPU" >&2; sleep 60; done; }
for try in 1 2 3 4 5 6; do
  G=$(pick); echo "### twopass long K=2 on GPU$G try=$try ($(date +%H:%M)) ###"
  if CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct K=2 CASES=long $PY eval_twopass.py; then break; fi
  echo "RETRY twopass try=$try"; sleep 90
done
echo "### TWOPASS DONE ###"
