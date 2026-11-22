#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python; NEED=34000
pick(){ while :; do for g in 1 0; do u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g|tr -d ' '); [ $((49140-u)) -ge $NEED ] && { echo $g; return; }; done; sleep 60; done; }
for try in 1 2 3 4 5 6; do
  G=$(pick); echo "### calib short K=2 on GPU$G try=$try ($(date +%H:%M)) ###"
  if CUDA_VISIBLE_DEVICES=$G MODEL=Qwen/Qwen2.5-14B-Instruct K=2 CASES=short $PY eval_calib.py; then break; fi
  echo "RETRY try=$try"; sleep 90
done
echo "### CALIB SHORT DONE ###"
