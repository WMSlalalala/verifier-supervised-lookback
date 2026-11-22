#!/bin/bash
# 长轨迹评估：断点续传 + GPU 等待 + OOM 自动重试
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=32000; MAXWAIT=14400; MAXRETRY=12
pick_gpu() {
  t=0
  while [ $t -lt $MAXWAIT ]; do
    for g in 1 0; do
      used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g | tr -d ' ')
      total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i $g | tr -d ' ')
      if [ $((total-used)) -ge $NEED ]; then echo $g; return 0; fi
    done
    [ $((t%600)) -eq 0 ] && echo "[$(date +%H:%M)] 等待 GPU (需 ${NEED}MiB; GPU0/1 空闲 $((49140-$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0|tr -d ' ')))/$((49140-$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1|tr -d ' '))))" >&2
    sleep 60; t=$((t+60))
  done
  echo "WAIT_TIMEOUT" >&2; return 1
}
for MODE in B; do
  NEED=28000
  for try in $(seq 1 $MAXRETRY); do
    G=$(pick_gpu) || exit 1
    echo "### 评估 $MODE on GPU$G try=$try ($(date +%H:%M)) ###"
    if CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct MODE=$MODE $PY eval_long.py; then break; fi
    echo "EVAL_${MODE}_RETRY try=$try"; sleep 90
    [ $try -eq $MAXRETRY ] && { echo "EVAL_${MODE}_FAILED"; exit 1; }
  done
done
echo "### LONG DONE ###"
