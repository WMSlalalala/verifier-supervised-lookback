#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
pick(){ NEED=$1; while :; do for g in 0 1; do [ $(free_of $g) -ge $((NEED+3000)) ] && { echo $g; return; }; done; sleep 120; done; }
for try in 1 2 3 4 5 6; do
  [ -s fullhist_foldext_probs.json ] && { echo "skip"; exit 0; }
  G=$(pick 26000); echo "### [GPU$G try$try $(date +%H:%M)] fullhist ext ###"
  CUDA_VISIBLE_DEVICES=$G FOLD=ext $PY train_fullhist.py && { echo "### FH_EXT DONE ###"; exit 0; }
  sleep 180
done; echo "FAIL fullhist ext"
