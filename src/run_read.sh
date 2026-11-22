#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
CUDA_VISIBLE_DEVICES=1 SRC=trained $PY read_scorer.py || exit 1
CUDA_VISIBLE_DEVICES=1 SRC=untrained $PY read_scorer.py || exit 1
echo "READ ALL DONE"
