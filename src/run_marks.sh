#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
for m in gold recent random; do CUDA_VISIBLE_DEVICES=1 SRC=trained HIST=1 MARK=$m $PY read_scorer.py || exit 1; done
echo "MARKS DONE"
