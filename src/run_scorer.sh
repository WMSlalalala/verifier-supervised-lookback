#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
for f in 0 1 2 3 4; do [ -s scorer_fold${f}_probs.json ] && continue; CUDA_VISIBLE_DEVICES=1 FOLD=$f $PY train_scorer.py || { echo "FOLD_FAIL $f"; exit 1; }; done
echo "SCORER DONE"
