#!/bin/bash
# 长轨迹评估续跑：每个重阶段前等任一 GPU 腾出 >=NEED MiB，再在该卡上跑
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
NEED=26000; MAXWAIT=14400
pick_gpu() {
  t=0
  while [ $t -lt $MAXWAIT ]; do
    for g in 1 0; do
      used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g | tr -d ' ')
      total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i $g | tr -d ' ')
      if [ $((total-used)) -ge $NEED ]; then echo $g; return 0; fi
    done
    [ $((t%600)) -eq 0 ] && echo "[$(date +%H:%M)] 等待 GPU (需 ${NEED}MiB)..." >&2
    sleep 60; t=$((t+60))
  done
  echo "WAIT_TIMEOUT" >&2; return 1
}
for MODE in B D; do
  G=$(pick_gpu) || exit 1
  echo "### 评估 $MODE on GPU$G ($(date +%H:%M)) ###"
  CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct MODE=$MODE $PY eval_long.py || { echo "EVAL_${MODE}_FAILED"; exit 1; }
done
echo "### LONG DONE ###"
