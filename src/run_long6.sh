#!/bin/bash
# B 评估：跨两卡切模型。等两卡(各留 2GB 余量)合计空闲 >= NEED，按当时空闲设每卡上限。断点续传+重试。
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=32500; HEAD=2000; MAXRETRY=40
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
for try in $(seq 1 $MAXRETRY); do
  t=0
  while :; do
    f0=$(free_of 0); f1=$(free_of 1); a0=$((f0-HEAD)); a1=$((f1-HEAD))
    [ $a0 -lt 0 ] && a0=0; [ $a1 -lt 0 ] && a1=0
    [ $((a0+a1)) -ge $NEED ] && break
    [ $((t%600)) -eq 0 ] && echo "[$(date +%H:%M)] 等待: 可用 GPU0=${a0} GPU1=${a1} 合计 $((a0+a1)) < ${NEED}MiB"
    sleep 60; t=$((t+60))
  done
  MM="{\"0\":\"$((a0/1024))GiB\",\"1\":\"$((a1/1024))GiB\"}"
  echo "### 评估 B 跨卡 try=$try ($(date +%H:%M)) MAXMEM=$MM ###"
  if CUDA_VISIBLE_DEVICES=0,1 MAXMEM="$MM" MODEL=Qwen/Qwen2.5-14B-Instruct MODE=B $PY eval_long.py; then echo "### LONG DONE ###"; exit 0; fi
  echo "EVAL_B_RETRY try=$try  已完成 $(wc -l < eval_long_B_partial.jsonl 2>/dev/null || echo 0)/127"; sleep 120
done
echo "EVAL_B_FAILED"; exit 1
