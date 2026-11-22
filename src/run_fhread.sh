#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
pick(){ NEED=$1; while :; do for g in 1 0; do [ $(free_of $g) -ge $((NEED+3000)) ] && { echo $g; return; }; done; sleep 120; done; }
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G SRC=trained PREFIX=fullhist HIST=1 $PY read_scorer.py || exit 1
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G SRC=trained PREFIX=fullhist $PY read_scorer.py || exit 1
echo "### FHREAD DONE ###"
