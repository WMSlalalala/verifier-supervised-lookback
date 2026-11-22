#!/bin/bash
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
G=${GPU:-0}
echo "===== A 训练过的全历史基线 ====="
for f in 0 1 2 3 4; do [ -s fullhist_fold${f}_probs.json ] && continue; CUDA_VISIBLE_DEVICES=$G FOLD=$f $PY train_fullhist.py || exit 1; done
echo "===== B1 消融：去掉距离特征 ====="
for f in 0 1 2 3 4; do [ -s scorer_nodist_fold${f}_probs.json ] && continue; CUDA_VISIBLE_DEVICES=$G FOLD=$f TAG=_nodist NODIST=1 $PY train_scorer.py || exit 1; done
echo "===== B2 消融：正例权重=1 ====="
for f in 0 1 2 3 4; do [ -s scorer_posw1_fold${f}_probs.json ] && continue; CUDA_VISIBLE_DEVICES=$G FOLD=$f TAG=_posw1 POSW=1 $PY train_scorer.py || exit 1; done
echo "===== B3 消融：3B 模型 ====="
for f in 0 1 2 3 4; do [ -s scorer_3B_fold${f}_probs.json ] && continue; CUDA_VISIBLE_DEVICES=$G FOLD=$f TAG=_3B MODEL=Qwen/Qwen2.5-3B-Instruct $PY train_scorer.py || exit 1; done
echo "===== C top-2 标注读取 ====="
CUDA_VISIBLE_DEVICES=$G SRC=trained HIST=1 MARK=top2 $PY read_scorer.py || exit 1
echo "### EXP DONE ###"
