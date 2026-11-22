#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
pick(){ NEED=$1; while :; do for g in 0 1; do [ $(free_of $g) -ge $((NEED+3000)) ] && { echo $g; return; }; done; sleep 120; done; }
for try in 1 2 3 4 5 6; do
  G=$(pick 34000); echo "### [GPU$G try$try $(date +%H:%M)] ext hist read ###"
  CUDA_VISIBLE_DEVICES=$G SRC=trained SET=_more HIST=1 $PY read_scorer.py && { echo "### EXT2 DONE ###"; exit 0; }
  sleep 180
done; echo "FAIL ext hist"
